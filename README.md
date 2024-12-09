# Welcome Home Furniture Bank System

A web-based system for managing furniture donations, orders, and deliveries for a furniture bank. The system helps coordinate between staff, clients, volunteers, and donors.

## Features

- User authentication with role-based access (Staff, Client, Volunteer, Donor)
- Donation management
- Order processing
- Item tracking and inventory management
- Volunteer delivery coordination
- Performance analytics and rankings

## API Endpoints

### Authentication
- `POST /api/login/`: Authenticate users and return role-specific dashboard redirects
- `POST /api/logout/`: End user session
- `POST /api/register/`: Register new users with specified roles

### Donation Management
- `POST /api/accept-donation/`: Staff can accept donations from registered donors
  - Handles item details, piece information, and location assignment

### Order Management
- `POST /api/start-order/`: Staff can initiate new orders for clients
- `POST /api/add-to-order/`: Add items to existing orders
- `POST /api/prepare-order/`: Update item locations for order preparation
- `POST /api/update-order-status/`: Update delivery status of orders
- `GET /api/search-orders/`: Search orders by ID or client username

### Item Management
- `GET /api/find-single-item/<item_id>/`: Get location details for specific items
- `GET /api/find-order-items/<order_id>/`: Get all items in a specific order
- `GET /api/get-categories/`: List available item categories
- `GET /api/get-available-items/`: Search available items by category

### Order Validation
- `POST /api/validate-order/`: Validate order details and client information

### Analytics
- `GET /api/category-rankings/`: View most popular item categories
- `GET /api/volunteer-rankings/`: View volunteer performance metrics

### Page Routes
- `/login/`: Login page
- `/register/`: Registration page
- `/staff-dashboard/`: Staff dashboard
- `/client-dashboard/`: Client dashboard
- `/start-order/`: Order initiation page
- `/add-to-order/`: Item addition page
- `/prepare-order/`: Order preparation page
- `/update-order/`: Order status update page
- `/accept-donation/`: Donation acceptance page
- `/volunteer-rankings/`: Volunteer performance page
- `/category-rankings/`: Category popularity page

## Database Connection

The system uses MySQL for data storage. Connection parameters:
- Host: localhost
- Database: welcome_home
- User: root

## Security Features

- CSRF protection on forms
- Password hashing with salt
- Role-based access control
- Session management

## Error Handling

All API endpoints include:
- Input validation
- Error status codes
- Descriptive error messages
- Transaction management for data integrity

## Frontend Integration

- HTML templates with embedded JavaScript
- CSRF token handling
- Async/await for API calls
- Local storage for maintaining state
- Form validation and error display

## Getting Started

1. Ensure MySQL is installed and running
2. Create database 'welcome_home'
3. Configure database connection parameters
4. Install required Python packages
5. Run Django migrations
6. Start the development server
