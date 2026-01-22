# SSLCommerz Payment Integration - Setup Guide

## Current Status: ⚠️ Demo Credentials Active

The payment system is using **demo/test credentials** which may have limitations. For full functionality, you need to register for SSLCommerz credentials.

## Quick Fix Options

### Option 1: Use SSLCommerz Test Credentials (Recommended for Testing)

1. **Register for a test account** at: https://developer.sslcommerz.com/registration/

2. **Get your credentials** from the merchant dashboard

3. **Update Django settings** in `mvpBackend/mvpbackend/settings.py`:
   ```python
   SSLCOMMERZ_STORE_ID = 'your_test_store_id'
   SSLCOMMERZ_STORE_PASSWD = 'your_test_password'
   ```

4. **Restart Django server**:
   ```bash
   cd d:\SoftwareMVP\mvpBackend
   python manage.py runserver
   ```

### Option 2: Use Environment Variables (Best Practice)

1. **Create `.env` file** in `d:\SoftwareMVP\mvpBackend\`:
   ```bash
   SSLCOMMERZ_STORE_ID=your_store_id
   SSLCOMMERZ_STORE_PASSWD=your_password
   SSLCOMMERZ_IS_SANDBOX=True
   ```

2. **Install python-decouple**:
   ```bash
   pip install python-decouple
   ```

3. **Restart Django server**

### Option 3: Continue with Demo (Limited Functionality)

The current demo credentials (`dmsrf680a241076e9d`) might work for basic testing but may have validation issues.

## Callback URLs Configuration

✅ **Already configured** to redirect to your Next.js frontend:
- Success: `http://localhost:3000/payment/success`
- Failure: `http://localhost:3000/payment/failure`
- Cancel: `http://localhost:3000/payment/cancel`

## Testing the Integration

1. **Ensure both servers are running**:
   - Django: `http://127.0.0.1:8000`
   - Next.js: `http://localhost:3000`

2. **Test the Buy Now button** on a product page

3. **Check console logs** for detailed error messages

## Common Issues

### "SSL Commerz validation failed"
- **Cause**: Invalid or demo credentials
- **Fix**: Register for proper test credentials from SSLCommerz

### "Failed to create order"
- **Cause**: Missing required order fields
- **Fix**: Already handled in current implementation

### "Network error"
- **Cause**: Django server not running
- **Fix**: Start Django server on port 8000

## SSLCommerz Test Card Details

Once you have proper credentials, use these test cards in sandbox:

**Visa:**
- Card: 4111 1111 1111 1111
- Expiry: Any future date
- CVV: Any 3 digits

**MasterCard:**
- Card: 5555 5555 5555 4444
- Expiry: Any future date
- CVV: Any 3 digits

## Production Deployment

1. Register for **production credentials** at SSLCommerz
2. Update URLs to your production domain
3. Set `SSLCOMMERZ_IS_SANDBOX=False`
4. Use environment variables for security

## Support

- SSLCommerz Documentation: https://developer.sslcommerz.com/
- Integration Guide: https://developer.sslcommerz.com/doc/v4/

---

**Current Implementation**: ✅ Complete and ready for proper credentials
