# Admin System Credentials

## Admin Login Details

**Username:** `admin`  
**Password:** `SlsW8SdaBUZS`

**Admin Login URL:** [/admin/login](https://remindhub-5.preview.emergentagent.com/admin/login)

## Important Notes

- This is a separate admin system, independent from regular user login
- Admin can view all users and their contact counts
- Admin can edit user details (name, email, phone number)
- Admin can manage subscriptions and credits for users
- Protected by built-in math captcha

## Features

### Admin Dashboard
- View total users count
- View total contacts across all users
- View active subscriptions
- User management table with:
  - User details (name, email, phone)
  - Contact count per user
  - Subscription status
  - WhatsApp & Email credits
  - Quick action buttons

### User Management
- **Edit User**: Update name, email, phone number
- **Manage Subscription**: 
  - Change subscription status (trial/active/expired/cancelled)
  - Adjust WhatsApp credits
  - Adjust Email credits
  - Toggle unlimited WhatsApp/Email

## Security
- Captcha-protected login
- Separate authentication from regular users
- JWT-based token authentication
- Admin-only access to management endpoints
