/* Copyright 2018 Intel Corporation

 Licensed under the Apache License, Version 2.0 (the "License");
 you may not use this file except in compliance with the License.
 You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

 Unless required by applicable law or agreed to in writing, software
 distributed under the License is distributed on an "AS IS" BASIS,
 WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 See the License for the specific language governing permissions and
 limitations under the License.
------------------------------------------------------------------------------*/

/*******************************************************************************
 * cookiejar_tp
 *
 * Cookie Jar Transaction Processor written in C++.
 ******************************************************************************/

#include <ctype.h>
#include <string.h>
#include <log4cxx/logger.h>
#include <log4cxx/basicconfigurator.h>
#include <log4cxx/level.h>
#include <sawtooth_sdk/sawtooth_sdk.h>
#include <sawtooth_sdk/exceptions.h>
#include <cryptopp/sha.h>
#include <cryptopp/filters.h>
#include <cryptopp/hex.h>
#include <iostream>
#include <string>
#include <sstream>
#include <utility>
#include <list>
#include <vector>

static const std::string DEFAULT_VALIDATOR_URL = "tcp://validator:4004";
static const std::string TRANSACTION_FAMILY_NAME = "cookiejar";
static const std::string TRANSACTION_FAMILY_VERSION = "1.0";

using namespace log4cxx;
static log4cxx::LoggerPtr logger(log4cxx::Logger::getLogger
    (TRANSACTION_FAMILY_NAME));

// Helper function: generate a SHA512 hash and return it as hex-encoded string.
static std::string sha512(const std::string& message) {
    std::string digest;
    CryptoPP::SHA512 hash;

    CryptoPP::StringSource hasher(message, true,
        new CryptoPP::HashFilter(hash,
          new CryptoPP::HexEncoder (
             new CryptoPP::StringSink(digest), false)));
    return digest;
}

// Helper function: de-tokenize std::string based on a delimiter.
std::vector<std::string> split(const std::string& str, char delimiter) {
    std::istringstream strStream(str);
    std::string token;
    std::vector<std::string> tokens;

    while (std::getline(strStream, token, delimiter)) {
        tokens.push_back(token);
    }
    return tokens;
}


/*******************************************************************************
 * CookieJarApplicator class
 *
 * Handles the processing of CookieJar transactions, which are either
 * "bake" or "eat" a number of cookies in a cookie jar.
 ******************************************************************************/
class CookieJarApplicator:  public sawtooth::TransactionApplicator {
 public:
    CookieJarApplicator(sawtooth::TransactionUPtr txn,
        sawtooth::GlobalStateUPtr state) :
        TransactionApplicator(std::move(txn), std::move(state)) { }

    // The Apply() function does most of the work for the transaction processor
    // by processing a transaction for the cookiejar transaction family.
    void Apply() {
        try {
            std::string action;
            int32_t amount;

            std::cout << "CookieJarApplicator::Apply\n";
            // Extract user public key from TransactionHeader
            std::string customer_pubkey = this->txn->header()->GetValue(
                sawtooth::TransactionHeaderSignerPublicKey);

            // Extract the raw payload data for this transaction as a string.
            const std::string& raw_data = this->txn->payload();

            // Extract the action and value from the payload string.
            // It has already been converted from Base64, but needs
            // deserializing.  It is simply stored as a CSV: action,amount.
            this->payloadToActionValue(raw_data, action, amount);

            std::cout << "Got: " << action << " and " << amount << "\n";

            // Validate the amount is non-negative.
            if (amount <= 0) {
                std::string error = "Invalid action: '" + action
                                      + "' with amount <= 0";
                throw sawtooth::InvalidTransaction(error);
            }

            // Choose what to do with the value, based on action:
            if (action == "bake") {
                this->doBake(customer_pubkey, amount);
            } else if (action == "eat") {
                this->doEat(customer_pubkey, amount);
            } else {
                std::string error = "Invalid action: '" + action + "'";
                throw sawtooth::InvalidTransaction(error);
            }
        } catch(std::exception& e) {
            std::cerr << "Unexpected exception exiting: " << std::endl;
            std::cerr << e.what() << std::endl;
        } catch(...) {
            std::cerr << "Exiting due to unknown exception." << std::endl;
        }
    }

 private:
    // Make a 70-character (35-byte) address to store and retrieve the state.
    // The first 6 characters is the TF prefix, which is the
    // first 6 characters of SHA-512("cookiejar"), a4d219.
    std::string MakeAddress(const std::string& customer_pubkey) {
        return sha512(TRANSACTION_FAMILY_NAME).substr(0, 6) +
            sha512(customer_pubkey).substr(0, 64);
    }

    // Extract values from the payload.
    // For this transaction family, the payload is simply encoded
    // as a CSV (action, amount).
    void payloadToActionValue(const std::string& payload,
                              std::string& action,
                              int32_t& value) {
         std::vector<std::string> vs = split(payload, ',');

         if (vs.size() == 2) {
             action = vs[0];
             value = std::stoi(vs[1]);
         } else {
             std::string error = "Invalid number of arguments: expected 2, got:"
                 + std::to_string(vs.size()) + "\n";
             throw sawtooth::InvalidTransaction(error);
         }
    }

    // Handle the CookieJar "bake" action.
    // This example ignores overflow.
    void doBake(const std::string& customer_pubkey,
                     const uint32_t& request_amount) {
        std::string stored_count_str;
        uint32_t customer_available_count = 0;

        // Generate the unique state address based on user's public key
        auto address = this->MakeAddress(customer_pubkey);
        LOG4CXX_DEBUG(logger, "CookieJarApplicator::doBake Key: "
            << customer_pubkey << " Address: " << address);

        // Get the value stored at the state address for this user
        if (this->state->GetState(&stored_count_str, address)) {
            std::cout << "Cookie count: " << stored_count_str << "\n";
            if (stored_count_str.length() != 0) {
                customer_available_count = std::stoi(stored_count_str);
            }
        } else {
            // If the state address doesn't exist we create a new cookie jar.
            std::cout << "This is the first time we baked cookies.\n"
                << "Creating a new cookie jar for user: "
                << customer_pubkey << std::endl;
        }

        // Increment cookies by amount, extracted from the payload.
        customer_available_count += request_amount;
        LOG4CXX_DEBUG(logger, "Storing new available cookies: "
                      << customer_available_count << " units");
        stored_count_str = std::to_string(customer_available_count);

        // Store the updated value in the user's unique state address.
        this->state->SetState(address, stored_count_str);
    }

    // Handle CookieJar "eat" action.
    void doEat(const std::string& customer_pubkey,
                    const uint32_t& request_amount) {
        auto address = this->MakeAddress(customer_pubkey);

        LOG4CXX_DEBUG(logger, "CookieJarApplicator::doEat Key: "
            << customer_pubkey << " Address: " << address);

        std::string stored_count_str;

        // Retrieve the cookies available in the cookie jar.
        uint32_t customer_available_count = 0;
        if (this->state->GetState(&stored_count_str, address)) {
            std::cout << "Available cookies: " << stored_count_str << "\n";
            customer_available_count = std::stoi(stored_count_str);
        } else {
            std::string error = "Action was 'eat', but address was"
                " not found in state for Key: " + customer_pubkey;
            throw sawtooth::InvalidTransaction(error);
        }

        if ((customer_available_count > 0) &&
                (customer_available_count >= request_amount)) {
            customer_available_count -= request_amount;
        } else {
            std::string error = "You don't have enough cookies to eat. " +
                customer_pubkey;
            throw sawtooth::InvalidTransaction(error);
        }

        // Encode the value back to a string for storage.
        LOG4CXX_DEBUG(logger, "Storing new available cookies:"
                      << customer_available_count << " units");
        stored_count_str = std::to_string(customer_available_count);
        this->state->SetState(address, stored_count_str);
    }
};


/*******************************************************************************
 * CookieJarHandler Class
 *
 * This class will be registered as the transaction processor handler
 * with validator.
 * It sets the namespace prefix, versions, TF, and transaction types
 * that can be handled by this TP via the Apply() method.
 ******************************************************************************/
class CookieJarHandler: public sawtooth::TransactionHandler {
 public:
    // Constructor generates namespace prefix.
    CookieJarHandler() {
        this->namespacePrefix = sha512(TRANSACTION_FAMILY_NAME).substr(0, 6);
        LOG4CXX_DEBUG(logger, "namespace:" << this->namespacePrefix);
    }

    // Return Transaction Family name string.
    std::string transaction_family_name() const {
        return std::string(TRANSACTION_FAMILY_NAME);
    }

    // Return Transaction Family version string.
    std::list<std::string> versions() const {
        return { TRANSACTION_FAMILY_VERSION };
    }

    // Return Transaction Family namespace 6-character prefix.
    std::list<std::string> namespaces() const {
        return { namespacePrefix };
    }

    sawtooth::TransactionApplicatorUPtr GetApplicator(
            sawtooth::TransactionUPtr txn,
            sawtooth::GlobalStateUPtr state) {
        return sawtooth::TransactionApplicatorUPtr(
            new CookieJarApplicator(std::move(txn), std::move(state)));
    }

 private:
    std::string namespacePrefix;
};


// Entry point function to setup and run the transaction processor.
int main(int argc, char** argv) {
    try {
        // Set up a simple configuration that logs on the console.
        BasicConfigurator::configure();
        // Set maximum logging verbosity.
        logger->setLevel(Level::getAll());

        // Create a transaction processor.

        // 1. connect to validator at DEFAULT_VALIDATOR_URL.
        sawtooth::TransactionProcessorUPtr processor(
            sawtooth::TransactionProcessor::Create(DEFAULT_VALIDATOR_URL));

        // 2. create a transaction handler for our CookieJar TF.
        sawtooth::TransactionHandlerUPtr transaction_handler(
            new CookieJarHandler());

        // 3. register the transaction handler with validator.
        processor->RegisterHandler(
            std::move(transaction_handler));

        // 4. run the transaction processor.
        processor->Run();

        return 0;
    } catch(std::exception& e) {
        std::cerr << "Unexpected exception exiting: " << std::endl;
        std::cerr << e.what() << std::endl;
    } catch(...) {
        std::cerr << "Exiting due to unknown exception." << std::endl;
    }

    return -1;
}
