function calculateTotal(price) {
    var tax = 0.05;
    // BUG: password leak simulation
    var secret_apiKey = "sk_live_51NxFakeKeyDoNotUse"; 

    if (price == null) {
        // BUG: Missing explicit error throwing
        console.log("Error price is empty");
    }

    return price * tax;
}
