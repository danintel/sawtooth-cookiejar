# Copyright 2018 Intel Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ------------------------------------------------------------------------------
"""
CookieJarClient class interfaces with Sawtooth through the REST API.
It accepts input from a client CLI/GUI/BUI or other interface.
"""

import hashlib
import base64
import time
import requests
import yaml

from sawtooth_signing import create_context
from sawtooth_signing import CryptoFactory
from sawtooth_signing import ParseError
from sawtooth_signing.secp256k1 import Secp256k1PrivateKey

from sawtooth_sdk.protobuf.transaction_pb2 import TransactionHeader
from sawtooth_sdk.protobuf.transaction_pb2 import Transaction
from sawtooth_sdk.protobuf.batch_pb2 import BatchList
from sawtooth_sdk.protobuf.batch_pb2 import BatchHeader
from sawtooth_sdk.protobuf.batch_pb2 import Batch


# The Transaction Family Name
FAMILY_NAME = 'cookiejar'
# TF Prefix is first 6 characters of SHA-512("cookiejar"), a4d219

def _hash(data):
    return hashlib.sha512(data).hexdigest()

class CookieJarClient(object):
    """Client Cookie Jar class

    Supports "bake", "eat", and "count" functions.
    """

    def __init__(self, base_url, key_file=None):
        """Initialize the client class.

           This is mainly getting the key pair and the TF prefix.
        """
        self._base_url = base_url

        if key_file is None:
            self._signer = None
            return

        try:
            with open(key_file) as key_fd:
                private_key_str = key_fd.read().strip()
        except OSError as err:
            raise Exception(
                'Failed to read private key {}: {}'.format( \
                    key_file, str(err)))

        try:
            private_key = Secp256k1PrivateKey.from_hex(private_key_str)
        except ParseError as err:
            raise Exception( \
                'Failed to load private key: {}'.format(str(err)))

        self._signer = CryptoFactory(create_context('secp256k1')) \
            .new_signer(private_key)

        self._public_key = self._signer.get_public_key().as_hex()

        # Address is 6-char TF prefix + hash of "mycookiejar"'s public key
        self._address = _hash(FAMILY_NAME.encode('utf-8'))[0:6] + \
            _hash(self._public_key.encode('utf-8'))[0:64]

    # For each CLI command, add a method to:
    # 1. Do any additional handling, if required
    # 2. Create a transaction and a batch
    # 2. Send to REST API
    def bake(self, value):
        """Bake @value cookies for the cookie jar."""
        return self._wrap_and_send("bake", value)

    def eat(self, value):
        """Eat @value cookies from the cookie jar."""
        try:
            ret_value = self._wrap_and_send("eat", value)
        except Exception:
            raise Exception('Encountered an error during eat')
        return ret_value

    def count(self):
        """Count the number of cookies in the cookie jar."""
        result = self._send_to_restapi("state/{}".format(self._address))
        try:
            return base64.b64decode(yaml.safe_load(result)["data"])
        except BaseException:
            return None

    def _send_to_restapi(self,
                         suffix,
                         data=None,
                         content_type=None):
        """Send a REST command to the Validator via the REST API.

           Called by count() &  _wrap_and_send().
           The latter caller is made on the behalf of bake() & eat().
        """
        if self._base_url.startswith("http://"):
            url = "{}/{}".format(self._base_url, suffix)
        else:
            url = "http://{}/{}".format(self._base_url, suffix)

        headers = {}

        if content_type is not None:
            headers['Content-Type'] = content_type

        try:
            if data is not None:
                result = requests.post(url, headers=headers, data=data)
            else:
                result = requests.get(url, headers=headers)

            if not result.ok:
                raise Exception("Error {}: {}".format(
                    result.status_code, result.reason))
        except requests.ConnectionError as err:
            raise Exception(
                'Failed to connect to {}: {}'.format(url, str(err)))
        except BaseException as err:
            raise Exception(err)

        return result.text

    def _wrap_and_send(self,
                       action,
                       *values):
        """Create a transaction, then wrap it in a batch.

           Even single transactions must be wrapped into a batch.
           Called by bake() and eat().
        """

        # Generate a CSV UTF-8 encoded string as the payload
        raw_payload = action

        for val in values:
            raw_payload = ",".join([raw_payload, str(val)])

        payload = raw_payload.encode()

        # Construct the address where we'll store our state
        address = self._address
        input_address_list = [address]
        output_address_list = [address]

        # Create a TransactionHeader
        header = TransactionHeader(
            signer_public_key=self._public_key,
            family_name=FAMILY_NAME,
            family_version="1.0",
            inputs=input_address_list,
            outputs=output_address_list,
            dependencies=[],
            payload_sha512=_hash(payload),
            batcher_public_key=self._public_key,
            nonce=time.time().hex().encode()
        ).SerializeToString()

        # Create a Transaction from the header and payload above
        transaction = Transaction(
            header=header,
            payload=payload,
            header_signature=self._signer.sign(header)
        )

        transaction_list = [transaction]

        # Create a BatchHeader from transaction_list above
        header = BatchHeader(
            signer_public_key=self._public_key,
            transaction_ids=[txn.header_signature for txn in transaction_list]
        ).SerializeToString()

        # Create Batch using the BatchHeader and transaction_list above
        batch = Batch(
            header=header,
            transactions=transaction_list,
            header_signature=self._signer.sign(header))

        # Create a Batch List from Batch above
        batch_list = BatchList(batches=[batch])

        # Send batch_list to the REST API
        return self._send_to_restapi("batches",
                                     batch_list.SerializeToString(),
                                     'application/octet-stream')

