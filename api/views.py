from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import hashlib
import json
import mysql.connector
import random
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth.decorators import login_required

def login_page(request):
    return render(request, 'login.html')  # Renders login.html

def register_page(request):
    return render(request, 'register.html')  # Renders register.html

def item_details_page(request):
    return render(request, 'item_details.html')  # Renders item_details.html

def order_details_page(request):
    return render(request, 'order_details.html')  # Renders 

def accept_donation_page(request):
    return render(request, 'accept_donation.html')  # Renders accept_donation.html

def start_order_page(request):
    return render(request, 'start_order.html')  # Renders start_order.html

def add_to_order_page(request):
    return render(request, 'add_to_order.html')  # Renders add_to_order.html

def prepare_order_page(request):
    return render(request, 'prepare_order.html')  # Renders prepare_order.html

def update_order_status_page(request):
    return render(request, 'update_order.html')  # Renders update_order.html

def find_order_items_page(request):
    return render(request, 'find_order_items.html')  # Renders find_order_items.html

#DASHBOARDS
def staff_dashboard_page(request):
    return render(request, 'staff_dashboard.html')  # Renders staff_dashboard.html

def client_dashboard_page(request):
    return render(request, 'client_dashboard.html')  # Renders client_dashboard.html

def volunteer_rankings_page(request):
    return render(request, 'volunteer_rankings.html')

#DB CONNECTION
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Chamundi@123",
        database="welcome_home"
    )

# Utility function to hash passwords with salt
def hash_password(password, salt):
    return hashlib.sha256((salt + password).encode()).hexdigest()

# Login API
@csrf_exempt
def login(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get('userName')
        password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            # Get user and their role
            query = """
                SELECT p.*, a.roleID 
                FROM Person p 
                JOIN Act a ON p.userName = a.userName 
                WHERE p.userName=%s
            """
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if not user:
                return JsonResponse({'error': 'User not found'}, status=404)

            stored_password = user['password']
            salt = username[:5]

            if hash_password(password, salt) == stored_password:
                # Set session data
                request.session['user_id'] = user['userName']
                request.session['role'] = user['roleID']

                # Determine redirect URL based on role
                redirect_url = {
                    'STAFF': '/staff-dashboard',
                    'CLIENT': '/client-dashboard',
                    'VOLUNTEER': '/volunteer-dashboard',
                    'DONOR': '/donor-dashboard'
                }.get(user['roleID'], '/login')

                return JsonResponse({
                    'message': 'Login successful',
                    'redirect': redirect_url,
                    'user': {
                        'username': user['userName'],
                        'role': user['roleID']
                    }
                }, status=200)
            else:
                return JsonResponse({'error': 'Invalid credentials'}, status=401)

        finally:
            cursor.close()
            conn.close()

@csrf_exempt
def logout(request):
    if request.method == "POST":
        try:
            # Clear the session data
            request.session.flush()
            return JsonResponse({"message": "Logout successful"}, status=200)
        except Exception as e:
            print(f"Error during logout: {e}")
            return JsonResponse({"error": "An error occurred during logout"}, status=500)

    return JsonResponse({"error": "Invalid request method"}, status=405)

# Register API
@csrf_exempt
def register(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get('userName')
        password = data.get('password')
        fname = data.get('fname')
        lname = data.get('lname')
        email = data.get('email')
        designation = data.get('designation')

        salt = username[:5]
        hashed_password = hash_password(password, salt)

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            query = "INSERT INTO Person (userName, password, fname, lname, email) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (username, hashed_password, fname, lname, email))
            conn.commit()

            query = "INSERT INTO Act (userName, roleID) VALUES (%s, %s)"
            cursor.execute(query, (username, designation))
            conn.commit()

            return JsonResponse({'message': 'Registration successful'}, status=201)

        finally:
            cursor.close()
            conn.close()

# Find Single Item API
def find_single_item(request, item_id):
    conn = get_db_connection()
    cursor = conn.cursor()  # Use the default cursor

    try:
        query = """
            SELECT 
                Piece.roomNum AS roomNum, 
                Piece.shelfNum AS shelfNum, 
                Location.shelfDescription AS shelfDescription 
            FROM 
                Piece 
            JOIN 
                Location 
            ON 
                Piece.roomNum = Location.roomNum AND Piece.shelfNum = Location.shelfNum 
            WHERE 
                Piece.ItemID = %s
        """
        print(item_id)
        cursor.execute(query, (item_id,))
        pieces = cursor.fetchall()  # Fetch all rows as tuples

        # Convert tuples to dictionaries manually
        column_names = [desc[0] for desc in cursor.description]  # Get column names from cursor description
        pieces_as_dicts = [dict(zip(column_names, row)) for row in pieces]

        if not pieces_as_dicts:
            return JsonResponse({'error': 'Item not found or no pieces available'}, status=404)

        return JsonResponse({'itemID': item_id, 'locations': pieces_as_dicts}, status=200)

    finally:
        cursor.close()
        conn.close()


# Find Order Items API
def find_order_items(request, order_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Get items in the order
        query_items_in_order = "SELECT ItemID FROM ItemIn WHERE orderID=%s"
        cursor.execute(query_items_in_order, (order_id,))
        items_in_order = cursor.fetchall()  # Returns a list of tuples

        if not items_in_order:
            return JsonResponse({'error': 'Order not found or no items in order'}, status=404)

        # Get item locations for each item in the order
        item_locations_query = "SELECT roomNum, shelfNum FROM Piece WHERE ItemID=%s"
        
        items_with_locations = []
        
        for item in items_in_order:
            item_id = item[0]  # Access the first element of the tuple (ItemID)
            cursor.execute(item_locations_query, (item_id,))
            locations = cursor.fetchall()

            # Convert locations into a readable format
            location_list = [{'roomNum': loc[0], 'shelfNum': loc[1]} for loc in locations]

            items_with_locations.append({'itemID': item_id, 'locations': location_list})

        return JsonResponse({'orderID': order_id, 'items': items_with_locations}, status=200)

    finally:
        cursor.close()
        conn.close()


#@csrf_exempt
def accept_donation(request):

    print("accept donation api invoked")
    if request.method == "POST":
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Parse input data
            data = json.loads(request.body)
            user_name = data.get("userName")  # Staff member username
            donor_id = data.get("donorID")  # Donor's username
            item_data = data.get("itemData")  # List of items donated
            pieces_data = data.get("piecesData")  # List of pieces for each item

            # Step 1: Check if the user is a staff member
            staff_check_query = """
                SELECT COUNT(*) 
                FROM Act 
                WHERE userName = %s AND roleID = 'staff'
            """
            cursor.execute(staff_check_query, (user_name,))
            is_staff = cursor.fetchone()[0]

            if not is_staff:
                return JsonResponse({"error": "User is not authorized to accept donations"}, status=403)

            # Step 2: Check if the donor is registered
            donor_check_query = """
                SELECT COUNT(*) 
                FROM Person 
                WHERE userName = %s
            """
            cursor.execute(donor_check_query, (donor_id,))
            is_donor_registered = cursor.fetchone()[0]

            if not is_donor_registered:
                return JsonResponse({"error": "Donor is not registered"}, status=404)

            # Step 3: Process each donated item and store in the database
            for item in item_data:
                i_description = item.get("description")
                photo = item.get("photo")
                color = item.get("color")
                is_new = item.get("isNew", True)
                has_pieces = item.get("hasPieces", False)
                material = item.get("material")
                main_category = item.get("mainCategory")
                sub_category = item.get("subCategory")

                # Insert into Item table and get the auto-incremented ItemID
                insert_item_query = """
                    INSERT INTO Item (iDescription, photo, color, isNew, hasPieces, material, mainCategory, subCategory)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(insert_item_query, (i_description, photo, color, is_new, has_pieces, material, main_category, sub_category))
                conn.commit()
                item_id = cursor.lastrowid  # Get the auto-incremented ItemID

                # Insert into DonatedBy table
                insert_donated_by_query = """
                    INSERT INTO DonatedBy (ItemID, userName, donateDate)
                    VALUES (%s, %s, CURDATE())
                """
                cursor.execute(insert_donated_by_query, (item_id, donor_id))
                conn.commit()

                # Step 4: Process pieces for this item (if applicable)
                if has_pieces:
                    for piece in pieces_data:
                        piece_num = piece.get("pieceNum")
                        p_description = piece.get("description")
                        length = piece.get("length")
                        width = piece.get("width")
                        height = piece.get("height")
                        room_num = piece.get("roomNum")
                        shelf_num = piece.get("shelfNum")
                        p_notes = piece.get("notes")

                        insert_piece_query = """
                            INSERT INTO Piece (ItemID, pieceNum, pDescription, length, width, height, roomNum, shelfNum, pNotes)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """
                        cursor.execute(insert_piece_query,
                                       (item_id, piece_num, p_description,
                                        length, width,
                                        height,
                                        room_num,
                                        shelf_num,
                                        p_notes))
                        conn.commit()

            return JsonResponse({"message": "Donation accepted successfully"}, status=201)

        except Exception as e:
            conn.rollback()
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def start_order(request):
    if request.method == "POST":
        try:
            user_name = request.POST.get("userName")
            client_user = request.POST.get("clientUser")

            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if staff member
            staff_check_query = """
                SELECT COUNT(*) 
                FROM Act 
                WHERE userName = %s AND roleID = 'staff'
            """
            cursor.execute(staff_check_query, (user_name,))
            is_staff = cursor.fetchone()[0]

            if not is_staff:
                return JsonResponse({"error": "User is not authorized"}, status=403)

            # Check if client exists
            client_check_query = """
                SELECT COUNT(*) 
                FROM Person 
                WHERE userName = %s
            """
            cursor.execute(client_check_query, (client_user,))
            is_valid_client = cursor.fetchone()[0]

            if not is_valid_client:
                return JsonResponse({"error": "Invalid client username"}, status=404)

            # Generate order ID and save it in session
            order_id = random.randint(1000, 9999)

            # Insert into Ordered table
            insert_order_query = """
                INSERT INTO Ordered (orderID, orderDate, supervisor, client)
                VALUES (%s, CURDATE(), %s, %s)
            """
            cursor.execute(insert_order_query, (order_id, user_name, client_user))
            conn.commit()

            return JsonResponse({"message": "Order started successfully", "orderID": order_id}, status=201)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def add_to_order(request):
    if request.method == "POST":
        try:
            order_id = request.POST.get("orderID")
            item_id = request.POST.get("itemID")

            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the item is already in the 'ItemIn' table
            query_check_item = """
                SELECT COUNT(*) 
                FROM ItemIn 
                WHERE ItemID = %s AND orderID = %s
            """
            cursor.execute(query_check_item, (item_id, order_id))
            is_already_ordered = cursor.fetchone()[0] > 0

            if is_already_ordered:
                return JsonResponse({"error": f"Item {item_id} is already in order {order_id}"}, status=400)

            # Insert item into ItemIn table
            insert_item_query = """
                INSERT INTO ItemIn (ItemID, orderID) 
                VALUES (%s, %s)
            """
            cursor.execute(insert_item_query, (item_id, order_id))
            conn.commit()

            return JsonResponse({"message": f"Item {item_id} added to order {order_id}"}, status=200)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def prepare_order(request):
    if request.method == "POST":
        print("prepare_order request.POST: ", request.POST)
        try:
            order_id = request.POST.get("orderID")  # Order ID to prepare
            holding_room = request.POST.get("roomNum")  # Holding room number
            holding_shelf = request.POST.get("shelfNum")  # Holding shelf number

            conn = get_db_connection()
            cursor = conn.cursor()

            # Update the location of all items in the given order
            update_location_query = """
                UPDATE Piece 
                SET roomNum = %s, shelfNum = %s 
                WHERE ItemID IN (
                    SELECT ItemID FROM ItemIn WHERE orderID = %s
                )
            """
            cursor.execute(update_location_query, (holding_room, holding_shelf, order_id))
            
            conn.commit()

            return JsonResponse({"message": f"Order {order_id} prepared for delivery"}, status=200)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"error": "Invalid request method"}, status=405)


def search_orders(request):
    if request.method == "GET":
        try:

            print("search_query: ", request.GET.get("query"))
            search_query = request.GET.get("query")  # Can be an orderID or client username

            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to search orders by orderID or client username
            query = """
                SELECT orderID, orderDate, client 
                FROM Ordered 
                WHERE orderID = %s OR client = %s
            """
            # Execute the query with the search query as both parameters
            cursor.execute(query, (search_query, search_query))
            orders = cursor.fetchall()

            # Format the response as a list of dictionaries
            response_data = [
                {"orderID": row[0], "orderDate": str(row[1]), "client": row[2]}
                for row in orders
            ]

            return JsonResponse({"orders": response_data}, status=200)

        except Exception as e:
            print(f"Error: {e}")  # Log the error for debugging
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def update_order_status(request):
    if request.method == "POST":
        try:
            user = request.user  # Get the current logged-in user
            print("user: ", user)
            order_id = request.POST.get("orderID")  # Order ID to update
            new_status = request.POST.get("status")  # New status for the order

            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the user is supervising this order
            supervisor_check_query = """
                SELECT COUNT(*) 
                FROM Ordered 
                WHERE orderID = %s AND supervisor = %s
            """
            cursor.execute(supervisor_check_query, (order_id, user.username))
            is_supervisor = cursor.fetchone()[0] > 0

            # Check if the user is delivering this order
            deliverer_check_query = """
                SELECT COUNT(*) 
                FROM Delivered 
                WHERE orderID = %s AND userName = %s
            """
            cursor.execute(deliverer_check_query, (order_id, user.username))
            is_deliverer = cursor.fetchone()[0] > 0

            # If the user is neither supervising nor delivering this order, deny access
            if not is_supervisor and not is_deliverer:
                return JsonResponse({"error": "You are not authorized to update this order."}, status=403)

            # Update the status of the order in the Delivered table
            update_status_query = """
                UPDATE Delivered 
                SET status = %s 
                WHERE orderID = %s AND userName = %s
            """
            cursor.execute(update_status_query, (new_status, order_id, user.username))
            
            conn.commit()
            return JsonResponse({"message": "Order status updated successfully"}, status=200)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"error": "Invalid request method"}, status=405)




@require_http_methods(["GET"])
def get_categories(request):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT DISTINCT 
                mainCategory,
                subCategory
            FROM 
                Item
            WHERE 
                mainCategory IS NOT NULL 
                AND subCategory IS NOT NULL
            ORDER BY 
                mainCategory, 
                subCategory
        """
        
        cursor.execute(query)
        categories = cursor.fetchall()
        
        # Debug print
        print("Categories from database:", categories)
        
        return JsonResponse({
            'categories': categories
        })
        
    except Exception as e:
        print("Error in get_categories:", str(e))  # Debug print
        return JsonResponse({
            'error': str(e)
        }, status=500)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@require_http_methods(["GET"])
def get_available_items(request):
    try:
        main_category = request.GET.get('mainCategory')
        sub_category = request.GET.get('subCategory')
        
        if not main_category or not sub_category:
            return JsonResponse({
                'error': 'Both mainCategory and subCategory are required'
            }, status=400)
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query using your actual schema
        query = """
            SELECT 
                i.ItemID,
                i.iDescription as Description,  -- Changed to match your schema
                i.color as Color,
                i.material as Material,
                i.isNew,
                CASE 
                    WHEN ii.ItemID IS NOT NULL THEN TRUE 
                    ELSE FALSE 
                END as isOrdered
            FROM 
                Item i
            LEFT JOIN 
                ItemIn ii ON i.ItemID = ii.ItemID
            WHERE 
                i.mainCategory = %s 
                AND i.subCategory = %s
            ORDER BY 
                i.ItemID
        """
        
        cursor.execute(query, (main_category, sub_category))
        items = cursor.fetchall()
        
        # Format the items for JSON response
        formatted_items = []
        for item in items:
            formatted_items.append({
                'ItemID': item['ItemID'],
                'Description': item['Description'] or '',  # Using iDescription
                'Color': item['Color'] or '',
                'Material': item['Material'] or '',
                'isNew': bool(item['isNew']),
                'isOrdered': bool(item['isOrdered'])
            })
        
        return JsonResponse({
            'items': formatted_items,
            'status': 'success'
        })
        
    except Exception as e:
        print(f"Error in get_available_items: {str(e)}")
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@require_http_methods(["POST"])
def add_to_order(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('orderID')
        item_id = data.get('itemID')
        
        if not order_id or not item_id:
            return JsonResponse({
                'error': 'Both orderID and itemID are required'
            }, status=400)
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if item is already in an order
        check_query = """
            SELECT 1 FROM ItemIn 
            WHERE ItemID = %s
        """
        cursor.execute(check_query, (item_id,))
        if cursor.fetchone():
            return JsonResponse({
                'error': 'Item is already in an order'
            }, status=400)
        
        # Add item to order
        insert_query = """
            INSERT INTO ItemIn (ItemID, orderID, found) 
            VALUES (%s, %s, FALSE)
        """
        cursor.execute(insert_query, (item_id, order_id))
        conn.commit()
        
        return JsonResponse({
            'message': 'Item added to order successfully'
        })
        
    except Exception as e:
        print(f"Error in add_to_order: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

@require_http_methods(["POST"])
def validate_order(request):
    try:
        data = json.loads(request.body)
        order_id = data.get('orderID')
        
        if not order_id:
            return JsonResponse({
                'error': 'Order ID is required'
            }, status=400)
            
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query to validate order and get client info
        query = """
            SELECT 
                o.orderID,
                CONCAT(p.fname, ' ', p.lname) as clientName
            FROM 
                Ordered o
                JOIN Person p ON o.client = p.userName
            WHERE 
                o.orderID = %s
        """
        
        cursor.execute(query, (order_id,))
        order = cursor.fetchone()
        
        if not order:
            return JsonResponse({
                'error': 'Invalid Order ID'
            }, status=404)
        
        return JsonResponse({
            'message': 'Order validated successfully',
            'orderID': order['orderID'],
            'clientName': order['clientName']
        })
        
    except Exception as e:
        print(f"Error in validate_order: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def category_rankings_page(request):
    return render(request, 'category_rankings.html')


@require_http_methods(["GET"])
def category_rankings(request):
    try:
        # Get time period from query parameters (default to last 30 days)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Base query for category rankings
        query = """
            SELECT 
                i.mainCategory,
                i.subCategory,
                COUNT(DISTINCT o.orderID) as order_count,
                COUNT(ii.ItemID) as item_count
            FROM 
                Item i
                JOIN ItemIn ii ON i.ItemID = ii.ItemID
                JOIN Ordered o ON ii.orderID = o.orderID
            WHERE 
                o.orderDate BETWEEN %s AND %s
            GROUP BY 
                i.mainCategory, 
                i.subCategory
            ORDER BY 
                order_count DESC, 
                item_count DESC
            LIMIT 10
        """
        
        # If dates not provided, use last 30 days
        if not start_date:
            cursor.execute("SELECT DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)")
            start_date = cursor.fetchone()['DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)']
        if not end_date:
            cursor.execute("SELECT CURRENT_DATE")
            end_date = cursor.fetchone()['CURRENT_DATE']
            
        cursor.execute(query, (start_date, end_date))
        rankings = cursor.fetchall()
        
        return JsonResponse({
            'start_date': start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date,
            'end_date': end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date,
            'rankings': rankings
        })
        
    except Exception as e:
        print(f"Error in category_rankings: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

def volunteer_rankings(request):
    try:
        # Get time period from query parameters (default to last 30 days)
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Query for volunteer rankings
        query = """
            SELECT 
                p.userName,
                CONCAT(p.fname, ' ', p.lname) as fullName,
                COUNT(DISTINCT d.orderID) as total_deliveries,
                SUM(CASE WHEN d.status = 'DELIVERED' THEN 1 ELSE 0 END) as completed_deliveries,
                COUNT(DISTINCT o.orderID) as total_orders
            FROM 
                Person p
                JOIN Delivered d ON p.userName = d.userName
                JOIN Ordered o ON d.orderID = o.orderID
            WHERE 
                d.date BETWEEN %s AND %s
            GROUP BY 
                p.userName, p.fname, p.lname
            ORDER BY 
                total_deliveries DESC,
                completed_deliveries DESC
            LIMIT 10
        """
        
        # If dates not provided, use last 30 days
        if not start_date:
            cursor.execute("SELECT DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)")
            start_date = cursor.fetchone()['DATE_SUB(CURRENT_DATE, INTERVAL 30 DAY)']
        if not end_date:
            cursor.execute("SELECT CURRENT_DATE")
            end_date = cursor.fetchone()['CURRENT_DATE']
            
        cursor.execute(query, (start_date, end_date))
        rankings = cursor.fetchall()
        
        return JsonResponse({
            'start_date': start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date,
            'end_date': end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date,
            'rankings': rankings
        })
        
    except Exception as e:
        print(f"Error in volunteer_rankings: {str(e)}")
        return JsonResponse({
            'error': str(e)
        }, status=500)
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()