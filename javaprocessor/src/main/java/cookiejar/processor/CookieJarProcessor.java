package main.java.cookiejar.processor;

import java.util.ArrayList;
import java.util.Collection;
import java.util.Map;
import java.util.logging.Logger;
import com.google.protobuf.ByteString;
import java.util.Collections;
import sawtooth.sdk.processor.State;
import sawtooth.sdk.processor.TransactionHandler;
import sawtooth.sdk.processor.TransactionProcessor;
import sawtooth.sdk.processor.Utils;
import sawtooth.sdk.processor.exceptions.InternalError;
import sawtooth.sdk.processor.exceptions.InvalidTransactionException;
import sawtooth.sdk.protobuf.TpProcessRequest;

public class CookieJarProcessor {
	private static final Logger logger = Logger.getLogger(CookieJarProcessor.class.getName());

	public static void main(String[] args) {
		// Check connection string to validator is passed in arguments.
		if (args.length != 1) {
			logger.info("Missing argument!! Please pass validator connection string");
		}
		// Connect to validator with connection string (tcp://validator:4004)
		TransactionProcessor cookieJarProcessor = new TransactionProcessor(args[0]);
		// Create simple wallet transaction handler and register with the validator
		cookieJarProcessor.addHandler(new CookieJarHandler());
		//start the transaction processor
		new Thread(cookieJarProcessor).start();
	}

}


/* ******************************************************************************
 * CookieJarHandler
 *
 * It handles the processing of operations(bake/eat/clear) supported by cookiejar application.
 * It sets the name space prefix, versions and transaction family name.
 * This is the place where you implement your transaction specific logic(Inside apply() method
 * 
 ***************************************************************************** */

class CookieJarHandler implements TransactionHandler {
	private final Logger logger = Logger.getLogger(CookieJarHandler.class.getName());
	private final static String VERSION = "1.0";
	private final static String TXN_FAMILY_NAME = "cookiejar";
	private final static int MAX_ARG_LENGTH = 2;
	private String COOKIEJAR_NAMESPACE;

	public CookieJarHandler() {
		try {
			// Initialize the cookie jar name space using first 6 characters
			COOKIEJAR_NAMESPACE = Utils.hash512(TXN_FAMILY_NAME.getBytes("UTF-8")).substring(0, 6);
			logger.info("Namespace = " +COOKIEJAR_NAMESPACE);
			logger.info("Transaction Family = "+TXN_FAMILY_NAME);
			logger.info("Version = "+VERSION);
		} catch (java.io.UnsupportedEncodingException ex) {
			System.out.println("Unsupported the encoding format ");
			ex.printStackTrace();
			System.exit(1);
		}
	}
	/*
     * apply()
     *
     * This method is invoked for each transaction the validator
     * gets from the client
     * 
     * @param: request - contains the transaction
     *                   
     * @param: stateInfo - contains the state context
     *
     * @returns: void
     *
     * @throws: InvalidTransactionException, InternalError
     *
     */
	@Override
	public void apply(TpProcessRequest request, State state) throws InvalidTransactionException, InternalError {
		// Get the user's signing public key from header
		String userPublicKey = request.getHeader().getSignerPublicKey();
		// Get the unique user address key derived from the user's signing public key
		String userAddress = getUserAddress(userPublicKey);
		logger.info("User Public Key = " + userPublicKey + " ; Address Key = " + userAddress);
		// Extract the payload as utf8 string from the transaction, in request variable
		String payload = request.getPayload().toStringUtf8();
	     // Split the csv utf-8 string
		String[] payloadList = payload.split(",");
		if (payloadList.length == 0 || payloadList.length > MAX_ARG_LENGTH) {
			throw new InvalidTransactionException(
					"Invalid no. of arguments: expected 1 or 2, got:" + payloadList.length);
		}
		// First argument from payload is operation name
		String operation = payloadList[0];
		logger.info("Requested operation = " +operation);
		Integer cookieCount = Integer.valueOf(payloadList[1]);

		switch (operation) {
		case "bake":
			bakeCookies(state, cookieCount, userPublicKey, userAddress);
			break;
		case "eat":
			eatCookies(state, cookieCount, userPublicKey, userAddress);
			break;
		case "clear":
			clearCookies(state, userPublicKey, userAddress);
			break;
			 /* Add here your custom operation to perform and make changes in client as well
		     * pass the corresponding operation name in the payload.
		     * */
		default:
			throw new InvalidTransactionException("unsupported operation : " + operation);
		}
	}

	@Override
	public Collection<String> getNameSpaces() {
		ArrayList<String> namespaces = new ArrayList<>();
		namespaces.add(COOKIEJAR_NAMESPACE);
		return namespaces;
	}

	@Override
	public String getVersion() {
		return VERSION;
	}

	@Override
	public String transactionFamilyName() {
		return TXN_FAMILY_NAME;
	}

	private String getUserAddress(String userPublicKey) {
		// Generate unique key(user address key) from the cookiejar namespace
        // and user signer public key
		return Utils.hash512(TXN_FAMILY_NAME.getBytes()).substring(0, 6)
				+ Utils.hash512(userPublicKey.getBytes()).substring(0, 64);
	}

	 /*
	    * bakeCookies()
	    *
	    * @param state - contains the state(the merkle tree), 
	    *
	    * @param cookieCount - the cookies to add to user's jar
	    *
	    * @param userPublicKey - the user's public key
	    *
	    * @param userAddress - the user's address key
	    *
	    * @returns - void
	    *
	    * @throws - InvalidTransactionException, InternalError
	    *
	 */
	private void bakeCookies(State state, Integer cookieCount, String userPublicKey, String userAddress)
			throws InternalError, InvalidTransactionException {

		// Get existing count from ledger state
		Map<String, ByteString> ledgerMap = state.getState(Collections.singletonList(userAddress));
		String currStateCount = ledgerMap.get(userAddress).toStringUtf8();
		logger.info("Baking " + cookieCount + " cookies");
		// getState() will return empty map if user address key doesn't exist in state
		if (currStateCount.isEmpty()) {
			 logger.info("No cookie jar availble");
			 logger.info("Creating a new jar for the user: " + userPublicKey);
		}else {
			cookieCount += Integer.valueOf(currStateCount);
		}
		// Update new count in the ledger state
		ledgerMap.put(userAddress, ByteString.copyFromUtf8(cookieCount.toString()));
		state.setState(ledgerMap.entrySet());
	}

	 /*
	    * eatCookies()
	    *
	    * @param state - contains the state(the merkle tree), 
	    *
	    * @param cookieCount - the cookies to add to user's jar
	    *
	    * @param userPublicKey - the user's public key
	    *
	    * @param userAddress - the user's address key
	    *
	    * @returns - void
	    *
	    * @throws - InvalidTransactionException, InternalError
	    *
	 */
	private void eatCookies(State state, Integer cookieCount, String userPublicKey, String userAddress)
			throws InternalError, InvalidTransactionException {
		
		// Get existing count from ledger state
		Map<String, ByteString> ledgerMap = state.getState(Collections.singletonList(userAddress));
		String currStateCount = ledgerMap.get(userAddress).toStringUtf8();
		// getState() will return empty map if user address key doesn't exist in state
		if (currStateCount.isEmpty()) {
			String error = "Didn't find the user address associated with user public key " + userPublicKey;
			throw new InvalidTransactionException(error);
		}
		Integer currCookieCount = Integer.valueOf(currStateCount);
		//insufficient cookies in jar
		if (currCookieCount < cookieCount) {
			String error = "Can only eat maximum of " + currCookieCount + " cookie(s)";
			throw new InvalidTransactionException(error);
		}
		currCookieCount -= cookieCount;
		logger.info("Eating " + cookieCount + " cookies");
		// Update new count in the ledger state
		ledgerMap.put(userAddress, ByteString.copyFromUtf8(currCookieCount.toString()));
		state.setState(ledgerMap.entrySet());
	}

	 /*
	    * clearCookies()
	    *
	    * @param state - contains the state(the merkle tree), 
	    *
	    * @param userPublicKey - the user's public key
	    *
	    * @param userAddress - the user's address key
	    *
	    * @returns - void
	    *
	    * @throws - InvalidTransactionException, InternalError
	    *
	 */
	private void clearCookies(State state, String userPublicKey, String userAddress)
			throws InternalError, InvalidTransactionException {
	
		// Get existing count from ledger state
		Map<String, ByteString> ledgerMap = state.getState(Collections.singletonList(userAddress));
		String currStateCount = ledgerMap.get(userAddress).toStringUtf8();
		// getState() will return empty map if user address key doesn't exist in state
		if (currStateCount.isEmpty()) {
			String error = "Didn't find the user address associated with user public key " + userPublicKey;
			throw new InvalidTransactionException(error);
		}
		logger.info("Clearing all " + currStateCount + " cookies");
		// Update new count in the ledger state with 0
		ledgerMap.put(userAddress, ByteString.copyFromUtf8("0"));
		state.setState(ledgerMap.entrySet());
	}

}
