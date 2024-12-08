from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
import hashlib
import json
import mysql.connector
import random
from django.shortcuts import render

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


#DASHBOARDS
def staff_dashboard_page(request):
    return render(request, 'staff_dashboard.html')  # Renders staff_dashboard.html

def client_dashboard_page(request):
    return render(request, 'client_dashboard.html')  # Renders client_dashboard.html



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


def accept_donation(request):
    if request.method == "POST":
        print("Accept Donation endpoint invoked")  # Debug print statement

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Parse input data
            user_name = request.POST.get("userName")  # Staff member username
            donor_id = request.POST.get("donorID")  # Donor's username
            item_description = request.POST.get("itemDescription")
            photo = request.POST.get("photo")
            color = request.POST.get("color")
            is_new = request.POST.get("isNew", "true").lower() == "true"
            has_pieces = request.POST.get("hasPieces", "false").lower() == "true"
            material = request.POST.get("material")
            main_category = request.POST.get("mainCategory")
            sub_category = request.POST.get("subCategory")

            print(f"Received data: user_name={user_name}, donor_id={donor_id}, item_description={item_description}")

            # Step 1: Check if the user is a staff member
            staff_check_query = """
                SELECT COUNT(*) 
                FROM Act 
                WHERE userName = %s AND roleID = 'staff'
            """
            cursor.execute(staff_check_query, (user_name,))
            is_staff = cursor.fetchone()[0]

            print(f"Is staff: {is_staff}")

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

            print(f"Is donor registered: {is_donor_registered}")

            if not is_donor_registered:
                return JsonResponse({"error": "Donor is not registered"}, status=404)

            # Step 3: Check if category exists in Category table
            category_check_query = """
                SELECT COUNT(*) 
                FROM Category 
                WHERE mainCategory = %s AND subCategory = %s
            """
            cursor.execute(category_check_query, (main_category, sub_category))
            category_exists = cursor.fetchone()[0]

            print(f"Does category exist: {category_exists}")

            # If category does not exist, insert it into Category table
            if not category_exists:
                insert_category_query = """
                    INSERT INTO Category (mainCategory, subCategory, catNotes)
                    VALUES (%s, %s, %s)
                """
                cursor.execute(insert_category_query, (main_category, sub_category, "Auto-generated by donation"))
                conn.commit()
                print(f"Inserted new category: {main_category} - {sub_category}")

            # Step 4: Insert item into Item table
            insert_item_query = """
                INSERT INTO Item (iDescription, photo, color, isNew, hasPieces, material, mainCategory, subCategory)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_item_query, (item_description, photo, color,
                                               is_new, has_pieces,
                                               material,
                                               main_category,
                                               sub_category))
            conn.commit()
            item_id = cursor.lastrowid  # Get the auto-incremented ItemID

            print(f"Inserted item with ID: {item_id}")

            # Step 5: Insert into DonatedBy table
            insert_donated_by_query = """
                INSERT INTO DonatedBy (ItemID, userName, donateDate)
                VALUES (%s, %s, CURDATE())
            """
            cursor.execute(insert_donated_by_query, (item_id, donor_id))
            conn.commit()

            print(f"Inserted donation record for item ID {item_id} by donor {donor_id}")

            # Step 6: Process pieces for this item (if applicable)
            if has_pieces:
                num_pieces = int(request.POST.get("numPieces", 0))
                print(f"Processing {num_pieces} pieces")

                for i in range(1, num_pieces + 1):
                    piece_num = i
                    p_description = request.POST.get(f"pieceDescription_{i}")
                    length = int(request.POST.get(f"length_{i}", 0))
                    width = int(request.POST.get(f"width_{i}", 0))
                    height = int(request.POST.get(f"height_{i}", 0))
                    room_num = int(request.POST.get(f"roomNum_{i}", 0))
                    shelf_num = int(request.POST.get(f"shelfNum_{i}", 0))
                    p_notes = request.POST.get(f"pNotes_{i}")

                    print(f"Inserting piece {piece_num}: room={room_num}, shelf={shelf_num}")

                    insert_piece_query = """
                        INSERT INTO Piece (ItemID, pieceNum, pDescription,
                                           length,
                                           width,
                                           height,
                                           roomNum,
                                           shelfNum,
                                           pNotes)
                        VALUES (%s, %s, %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s,
                                %s)
                    """
                    cursor.execute(insert_piece_query,
                                   (item_id,
                                    piece_num,
                                    p_description,
                                    length,
                                    width,
                                    height,
                                    room_num,
                                    shelf_num,
                                    p_notes))
                    conn.commit()

                    print(f"Inserted piece {piece_num} for item ID {item_id}")

            return JsonResponse({"message": "Donation accepted successfully"}, status=201)

        except Exception as e:
            conn.rollback()
            print(f"Error: {e}")  # Log the error for debugging
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


from django.http import JsonResponse

def get_categories(request):
    if request.method == "GET":
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to fetch all categories and subcategories
            query = """
                SELECT mainCategory, subCategory 
                FROM Category
            """
            cursor.execute(query)
            categories = cursor.fetchall()

            # Format the response as a list of dictionaries
            response_data = [{"mainCategory": row[0], "subCategory": row[1]} for row in categories]

            return JsonResponse({"categories": response_data}, status=200)

        except Exception as e:
            print(f"Error: {e}")
            return JsonResponse({"error": str(e)}, status=500)

        finally:
            cursor.close()
            conn.close()

    return JsonResponse({"error": "Invalid request method"}, status=405)


def get_available_items(request):
    if request.method == "GET":
        try:
            main_category = request.GET.get("mainCategory")
            sub_category = request.GET.get("subCategory")

            conn = get_db_connection()
            cursor = conn.cursor()

            # Query to fetch items in the given category/subcategory that are not yet ordered
            query = """
                SELECT ItemID, iDescription, color, material 
                FROM Item 
                WHERE mainCategory = %s AND subCategory = %s 
                AND ItemID NOT IN (SELECT ItemID FROM ItemIn)
            """
            cursor.execute(query, (main_category, sub_category))
            items = cursor.fetchall()

            # Format the response as a list of dictionaries
            response_data = [
                {"ItemID": row[0], "iDescription": row[1], "color": row[2], "material": row[3]}
                for row in items
            ]

            return JsonResponse({"items": response_data}, status=200)

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
            order_id = request.POST.get("orderID")  # Order ID from session or frontend
            item_id = request.POST.get("itemID")  # Item ID to add

            conn = get_db_connection()
            cursor = conn.cursor()

            # Check if the item is already in the 'ItemIn' table for this order
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