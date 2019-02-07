#!/usr/bin/env python3

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
'''
CookieJarTransactionHandler class interfaces for cookiejar Transaction Family.
'''

import traceback
import sys
import hashlib
import logging

from sawtooth_sdk.processor.handler import TransactionHandler
from sawtooth_sdk.processor.exceptions import InvalidTransaction
from sawtooth_sdk.processor.exceptions import InternalError
from sawtooth_sdk.processor.core import TransactionProcessor

from sys import path
path.append('../proto')
from cookiejar_pb2 import CookiejarTransaction

# hard-coded for simplicity (otherwise get the URL from the args in main):
#DEFAULT_URL = 'tcp://localhost:4004'
# For Docker:
DEFAULT_URL = 'tcp://validator:4004'

LOGGER = logging.getLogger(__name__)

FAMILY_NAME = "cookiejar"
# TF Prefix is first 6 characters of SHA-512("cookiejar"), a4d219

def _hash(data):
    '''Compute the SHA-512 hash and return the result as hex characters.'''
    return hashlib.sha512(data).hexdigest()

def _get_cookiejar_address(from_key):
    '''
    Return the address of a cookiejar object from the cookiejar TF.

    The address is the first 6 hex characters from the hash SHA-512(TF name),
    plus the result of the hash SHA-512(cookiejar public key).
    '''
    return _hash(FAMILY_NAME.encode('utf-8'))[0:6] + \
                 _hash(from_key.encode('utf-8'))[0:64]


class CookieJarTransactionHandler(TransactionHandler):
    '''
    Transaction Processor class for the cookiejar Transaction Family.

    This TP communicates with the Validator using the accept/get/set functions.
    This implements functions to "bake" or "eat" cookies in a cookie jar.
    '''
    def __init__(self, namespace_prefix):
        '''Initialize the transaction handler class.

           This is setting the "cookiejar" TF namespace prefix.
        '''
        self._namespace_prefix = namespace_prefix

    @property
    def family_name(self):
        '''Return Transaction Family name string.'''
        return FAMILY_NAME

    @property
    def family_versions(self):
        '''Return Transaction Family version string.'''
        return ['1.0']

    @property
    def namespaces(self):
        '''Return Transaction Family namespace 6-character prefix.'''
        return [self._namespace_prefix]

    def apply(self, transaction, context):
        '''This implements the apply function for the TransactionHandler class.

           The apply function does most of the work for this class by
           processing a transaction for the cookiejar transaction family.
        '''

        # Get the payload and extract the cookiejar-specific information.
        # It has already been converted from Base64, but needs deserializing.
        # It was serialized with Protobuf: string action, uint32 amount
        header = transaction.header
        cookie = CookiejarTransaction()
        cookie.ParseFromString(transaction.payload)
        action = cookie.action
        amount = str(cookie.amount)

        # Get the signer's public key, sent in the header from the client.
        from_key = header.signer_public_key

        # Perform the action.
        LOGGER.info("Action = %s.", action)
        LOGGER.info("Amount = %s.", amount)
        if action == "bake":
            self._make_bake(context, amount, from_key)
        elif action == "eat":
            self._make_eat(context, amount, from_key)
        elif action == "clear":
            self._empty_cookie_jar(context, amount, from_key)
        else:
            LOGGER.info("Unhandled action. Action should be bake or eat")

    @classmethod
    def _make_bake(cls, context, amount, from_key):
        '''Bake (add) "amount" cookies.'''
        cookiejar_address = _get_cookiejar_address(from_key)
        LOGGER.info('Got the key %s and the cookiejar address %s.',
                    from_key, cookiejar_address)
        state_entries = context.get_state([cookiejar_address])
        new_count = 0

        if state_entries == []:
            LOGGER.info('No previous cookies, creating new cookie jar %s.',
                        from_key)
            new_count = int(amount)
        else:
            try:
                count = int(state_entries[0].data)
            except:
                raise InternalError('Failed to load state data')
            new_count = int(amount) + int(count)

        state_data = str(new_count).encode('utf-8')
        addresses = context.set_state({cookiejar_address: state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    @classmethod
    def _make_eat(cls, context, amount, from_key):
        '''Eat (subtract) "amount" cookies.'''
        cookiejar_address = _get_cookiejar_address(from_key)
        LOGGER.info('Got the key %s and the cookiejar address %s.',
                    from_key, cookiejar_address)

        state_entries = context.get_state([cookiejar_address])
        new_count = 0

        if state_entries == []:
            LOGGER.info('No cookie jar with the key %s.', from_key)
        else:
            try:
                count = int(state_entries[0].data)
            except:
                raise InternalError('Failed to load state data')
            if count < int(amount):
                raise InvalidTransaction('Not enough cookies to eat. '
                                         'The number should be <= %s.', count)
            else:
                new_count = count - int(amount)

        LOGGER.info('Eating %s cookies out of %d.', amount, count)
        state_data = str(new_count).encode('utf-8')
        addresses = context.set_state(
            {_get_cookiejar_address(from_key): state_data})

        if len(addresses) < 1:
            raise InternalError("State Error")

    @classmethod
    def _empty_cookie_jar(cls, context, amount, from_key):
        cookie_jar_address = _get_cookiejar_address(from_key)
        LOGGER.info("fetched key %s and state address %s", from_key, cookie_jar_address)
        state_entries = context.get_state([cookie_jar_address])
        if state_entries == []:
            LOGGER.info('No cookie jar with the key %s.', from_key)
            return
        else:
            state_data = str(0).encode('utf-8')
            addresses = context.set_state(
                {cookie_jar_address: state_data})

        if len(addresses) < 1:
            raise InternalError("State update Error")
        LOGGER.info("SET global state success")

def main():
    '''Entry-point function for the cookiejar Transaction Processor.'''
    try:
        # Setup logging for this class.
        logging.basicConfig()
        logging.getLogger().setLevel(logging.DEBUG)

        # Register the Transaction Handler and start it.
        processor = TransactionProcessor(url=DEFAULT_URL)
        sw_namespace = _hash(FAMILY_NAME.encode('utf-8'))[0:6]
        handler = CookieJarTransactionHandler(sw_namespace)
        processor.add_handler(handler)
        processor.start()
    except KeyboardInterrupt:
        pass
    except SystemExit as err:
        raise err
    except BaseException as err:
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
