import datetime

import pymysql
from prettytable import PrettyTable
import time


def main():
    username = input('Enter the username:')
    passwordValue = input('Enter the password:')
    # connect to the database
    try:

        mydb = pymysql.connect(
            host="localhost",
            user=username,
            password=passwordValue,
            database="airport"
        )



        while (True):
        # ask the user what they want to do
            print("Welcome to the database. What would you like to do?")
            print("1. Login--->1")
            print("2. Staff Login--->2")
            print("3. Register---->3")
            choice = input("Enter your choice: ")
            str = choice.lower()
            if str == "1":
                login(mydb)

            elif str == "2":
                staff(mydb)
            elif str == "3":
                register(mydb)
            else:
                print("Invalid choice please try again")
    except pymysql.err.OperationalError as e:
        print('Error thrown while connecting to db: %d: %s' % (e.args[0], e.args[1]))
def dateValidation(date_string):
    try:
        time.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def flightSchedules(date_string,mydb):
    cursor = mydb.cursor()
    cursor.callproc("getAllFlightSchedulesForADate", [date_string])
    result = cursor.fetchone()
    cursor.close()
    return result
def book(mydb,email):
    while True:
        view_date = input("Enter the date in YYYY-MM-DD format: ")
        if not dateValidation(view_date):
            print("Invalid date format. Please enter the date again in YYYY-MM-DD format.")
        else:
            result = flightSchedules(view_date,mydb)
            if result:
                break
            else:
                print("No schedules for this date. Please enter the date again.")

    try:
        cursor = mydb.cursor()
        origin = []
        destination =[]
        cursor.callproc("getAllFlightSchedulesForADate", [view_date])
        rows = cursor.fetchall()
        schedule_list = []
        cursor.close()
        for r in rows:
            schedule_list.append(r[0])
            origin.append(r[2])
            destination.append(r[3])
        print("Select origin and destination from the list")
        print(origin)
        print(destination)
        og = input("Enter the origin:")
        while og not in origin:
            print("entered origin name does not exist. Please enter again")
            og = input("Enter the origin:")
        ds = input("Enter the destination:")
        while ds not in destination:
            print("entered destination name does not exist. Please enter again")
            ds = input("Enter the destination:")
        cursor = mydb.cursor()
        cursor.callproc("findFlights", [view_date, og, ds])
        columns = [desc[0] for desc in cursor.description]
        table = PrettyTable(columns)
        rows = cursor.fetchall()
        cursor.close()

        if not rows:
            print("Sorry, no schedule exists for the given origin and destination on this date.")
        else:
            for row in rows:
                table.add_row(row)
            print(table)

            schedule_id = input("Enter the schedule id you want to book: ")
            while(True):
                if int(schedule_id) not in schedule_list:
                    schedule_id = input("Enter the schedule id you want to book: From the above shown Schedule id's")
                else:
                    break
            choice = input("Do you want to confirm booking the ticket: Yes/No:")
            str = choice.lower()
            if str == "yes":
                try:
                    cursor = mydb.cursor()
                    cursor.execute("SELECT bookTicket(%s, %s)", (schedule_id, email))

                    result2 = cursor.fetchone()
                    mydb.commit()
                    cursor.close()
                    print("Ticket booked successfully!")
                    print("View Your Bookings : Yes/No")
                    choice = input("Enter your choice: ")
                    str = choice.lower()
                    if str == "yes":
                        try:
                            cursor = mydb.cursor()
                            cursor.callproc("findAllUserBookings", [email])
                            mydb.commit()
                            columns = [desc[0] for desc in cursor.description]
                            table = PrettyTable(columns)
                            rows = cursor.fetchall()
                            cursor.close()
                            for row in rows:
                                table.add_row(row)
                            print(table)
                        except Exception as e:
                            print("An error occurred while searching the booked flight details by passenger: ",
                              e)
                    elif str == "no":
                        print("Enjoy Your Journey!")
                    else:
                        print("Sorry! Invalid Input")

                except Exception as e:
                    print("An error occurred while booking the flight using bookTicket function: ", e)
            elif str == "no":
                print("Taking you back to the Dashboard.")
            else:
                print("Sorry! Invalid Input")
    except Exception as e:
        print("An error occurred searching the flight details for booking: ", e)


def view(mydb, email):
    while True:
        try:
            cursor = mydb.cursor()
            cursor.callproc("findAllUserBookings", [email])
            mydb.commit()
            columns = [desc[0] for desc in cursor.description]
            table = PrettyTable(columns)
            rows = cursor.fetchall()
            cursor.close()
            for row in rows:
                table.add_row(row)
            print(table)
            if any(row[3] is None for row in rows):
                print("Sorry, no bookings available to view.")
                break
            else:
                print("What would you like to do?")
                print("1.Update a booking ---> 1")
                print("2.Cancel a booking ---> 2")
                print("3.Go back to Dashboard ---->3")
                choice = input("Please enter your choice of action :")
                str = choice.lower()
                if str == "1":
                    booking_id = []
                    option = input("Please retype the booking id that you want to update")

                    try:
                        cursor = mydb.cursor()
                        cursor.callproc("getAllBookingId",[email])
                        rows = cursor.fetchall()
                        cursor.close()
                        for row in rows:
                            booking_id.append(row[0])
                        while int(option) not in booking_id:
                            print("Sorry not a valid booking_id")
                            option = input("Please retype the booking id that you want to update")
                    except Exception as e:
                            print("An error occurred: ", e)
                    try:
                        schedule_id_list=[]
                        cursor = mydb.cursor()
                        cursor.callproc("getDetails",[option])
                        resultnew = cursor.fetchone();
                        dept_city = resultnew[0]
                        arr_city = resultnew[1]
                        date_of_dept = resultnew[2]
                        cursor.callproc("findFlights",[date_of_dept, dept_city, arr_city])
                        columns = [desc[0] for desc in cursor.description]
                        table = PrettyTable(columns)
                        rows = cursor.fetchall()
                        for row in rows:
                            table.add_row(row)
                            schedule_id_list.append(row[0])

                        print(table)
                        schedule_id = input("Enter the schedule id you want to book: ")
                        while int(schedule_id) not in schedule_id_list:
                            print("Cannot update to this schedule")
                            schedule_id = input("Enter the schedule id you want to book: ")
                        try:
                            cursor.execute("SELECT updateTicket(%s, %s,%s)", (schedule_id, email, option))
                            result2 = cursor.fetchone()
                            cursor.close()

                            print("Booking updated")
                        except Exception as e:
                            print(
                        "An error occurred while updating the booked flight ticket by calling updateTicket() function: ",
                        e)
                    except Exception as e:
                        print("An error occurred while updating the booked flight: ", e)
                elif choice == "2":
                    try:
                        cursor = mydb.cursor()
                        booking_id_list = []
                        ch = input("Enter the booking you want to cancel:")
                        cursor.callproc("getAllBookingId",[email])
                        rows = cursor.fetchall()
                        for row in rows:
                            booking_id_list.append(row[0])
                        while int(ch) not in booking_id_list:
                            print("Sorry not a valid booking_id")
                            ch = input("Please retype the booking id that you want to Cancel")
                        sure = input("Are you sure you want yo cancel this booking: YES/NO:")
                        if sure.lower() == "yes":
                            try:
                                cursor = mydb.cursor()
                                cursor.execute("SELECT deleteTicket(%s,%s)", (ch, email))
                                result2 = cursor.fetchone()
                                cursor.close()

                                print("Booking deleted")

                            except Exception as e:
                                print(
                        "An error occurred while deleting the booked flight ticket by calling deleteTicket() function: ",
                        e)
                        elif sure.lower() == "no":
                            print("Delete Cancelled")
                    except Exception as e:
                            print("An error occurred: ", e)
                elif str == "3":
                    break
                else:
                    print("Sorry not a valid option")
                    break

        except Exception as e:
            print("An error occurred while searching the booked flight details by passenger: ", e)


def updateDetails(mydb, email):
    print("Select from the following to update")
    print("1.Name ----->1")
    print("2.City ----->2")
    print("3.Email ----->3")
    print("4.Password ----->4")

    choicenew = input("Select the details you want to update:")
    if choicenew.lower() == "1":
        newname = input("Enter the new name:")
        try:
            cursor = mydb.cursor()
            cursor.execute("select updateUserName(%s,%s)",
                           (email, newname))
            mydb.commit()
            cursor.close()
            print("Updated Name Succesfully")
        except Exception as e:
            print("An error occurred while updating passenger details ", e)
    elif choicenew.lower() == "2":
        newpassword = input("Enter the new password")
        try:
            cursor = mydb.cursor()
            cursor.execute("select updateUserPassword(%s,%s)",
                           (email, newpassword))
            mydb.commit()
            cursor.close()
            print("Updated Password Succesfully")
        except Exception as e:
            print("An error occurred while updating passenger details ", e)
    elif choicenew.lower() == "3":
        newemail = input("Enter the new email")
        try:
            cursor = mydb.cursor()
            cursor.execute("select updateUserEmail(%s,%s)",
                           (email, newemail))
            mydb.commit()
            cursor.close()
            print("Updated Email Succesfully")
        except Exception as e:
            print("An error occurred while updating passenger details ", e)
    elif choicenew.lower() == "2":
        newcity = input("Enter the new city")
        print(newcity)
        try:
            cursor = mydb.cursor()
            cursor.execute("select updateUserCity(%s,%s)",
                           (email, newcity))
            mydb.commit()
            cursor.close()
            print("Updated City Succesfully")
        except Exception as e:
            print("An error occurred while updating passenger details ", e)
    else:
        print("Sorry not a valid option")

def login(mydb):
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    try:
        # check if the email and password are correct
        cursor = mydb.cursor()
        cursor.execute("SELECT * FROM passengers WHERE email = %s AND passoword = %s", (email, password))
        result = cursor.fetchone()
        cursor.close()
        while(True):
            print("Login successful!")
            if(result):
                name = result[1]
                print(f"Welcome, to the dashboard  {name}!. What would you like to do?")
                print("1. Book Tickets ---> 1")
                print("2. View Your Bookings ----> 2")
                print("3. Update user details---> 3")
                print("4. Logout---> 4")
                choice = input("Enter your choice: ")
                str = choice.lower()
                if str=="1":
                    book(mydb,email)
                elif str=="2":
                    view(mydb,email)
                elif str=="3":
                    updateDetails(mydb,email)
                elif str=="4":
                    print("Log out Successful!! Please login again to continue...")
                    break
            else:
                print("Login Credentials do not match. Register if New User or try Login again")
                break
    except ValueError as error:
        print("Error: ", error)


def searchEmployee(mydb):
    email = input("Enter the email of the passenger you want to search:")
    email_list=[]
    try:
        cursor = mydb.cursor()
        cursor.callproc("getAllEmails")
        rows= cursor.fetchall()
        cursor.close()
        for r in rows:
            email_list.append(r[0])
        if email not in email_list:
            print("Sorry this email does not exist")
        else:
            cursor = mydb.cursor()
            cursor.callproc("searchPassenger", [email])
            mydb.commit()

            columns = [desc[0] for desc in cursor.description]
            table = PrettyTable(columns)
            rows = cursor.fetchall()
            cursor.close()
            for row in rows:
                table.add_row(row)
            print(table)
    except Exception as e:
        print("An error occurred while searching the passenger: ", e)


def booksearch(mydb):
    email = input("Enter the email of the passenger you want to search:")
    email_list=[]
    try:
        cursor = mydb.cursor()
        cursor.callproc("getAllEmails")
        rows= cursor.fetchall()
        for r in rows:
            email_list.append(r[0])
        if email not in email_list:
            print("Sorry this email does not exist")
        else:
            cursor.callproc("findAllUserBookings", [email])
            mydb.commit()

            columns = [desc[0] for desc in cursor.description]
            table = PrettyTable(columns)
            rows = cursor.fetchall()
            cursor.close()
            for row in rows:
                table.add_row(row)
            print(table)
    except Exception as e:
        print(
            "An error occurred while searching the passenger booking by calling procedure findAllUserBookings : ",
            e)


def flightSearch(mydb):

    s_id_list= []
    try:
        cursor = mydb.cursor()
        cursor.callproc("getAllSchedules")
        rows= cursor.fetchall()
        for r in rows:
            s_id_list.append(r[0])
        print(s_id_list)
        s_id = input("Enter the schedule_id of the flight:")
        print(s_id)
        cursor.callproc("findAllPassengers", [s_id])
        mydb.commit()
        columns = [desc[0] for desc in cursor.description]
        table = PrettyTable(columns)
        rows = cursor.fetchall()
        cursor.close()
        for row in rows:
            table.add_row(row)
        print(table)

    except Exception as e:
        print("An error occurred while searching the flight: ", e)


def deleteSchedule(mydb):
    cursor = mydb.cursor()

    try:
        cursor.callproc("getAllSchedules")
        rows = cursor.fetchall()
        allSchedules = []
        for row in rows:
            allSchedules.append(row[0])
        print(allSchedules)
        s_id = input("Enter the schedule you want to delete")
        if(int(s_id) in allSchedules):
            cursor.callproc("deleteBookings", [s_id])
            mydb.commit()
            cursor.close()
            print("Schedule deleted")
        else:
            print("Sorry given schedule does not exist")
    except Exception as e:
        print("An error occurred while deleting the schedule: ", e)


def createSchedule(mydb):
    try:
        new_list = []
        cursor = mydb.cursor()
        cursor.callproc("getAllRoutes")
        columns = [desc[0] for desc in cursor.description]
        table = PrettyTable(columns)
        rows = cursor.fetchall()
        for row in rows:
            new_list.append(row[0])
            table.add_row(row)
        print(table)

        # Get valid route id from user
        while True:
            r_id = input("Select a route id for the route you want to add a new schedule for: ")
            if r_id in new_list:
                break
            else:
                print("Invalid input. Please select a valid route id from the displayed Routes.")

        cursor.callproc("getAllAircrafts")
        rows = cursor.fetchall()
        new_list = []
        for r in rows:
            new_list.append(r[0])
        print(new_list)

        while True:
            a_id = input("Select an aircraft for the new schedule: ")
            if a_id in new_list:
                break
            else:
                print("Invalid input. Please select a valid aircraft id from the displayed list.")

        # Get valid departure time from user
        while True:
            d_time = input("Enter the departure date and time in the format YYYY-MM-DD HHH:MM:SS: ")
            try:
                datetime.datetime.strptime(d_time, '%Y-%m-%d %H:%M:%S')
                break
            except ValueError:
                print("Invalid input. Please enter a valid date and time in the specified format.")

        # Get valid arrival time from user
        while True:
            a_time = input("Enter the arrival date and time in the format YYYY-MM-DD HHH:MM:SS: ")
            try:
                datetime.datetime.strptime(a_time, '%Y-%m-%d %H:%M:%S')
                break
            except ValueError:
                print("Invalid input. Please enter a valid date and time in the specified format.")

        # Get valid number of tickets left from user
        while True:
            t_left = input("Enter the number of tickets left: ")
            if t_left.isdigit():
                break
            else:
                print("Invalid input. Please enter a valid integer for the number of tickets left.")

        # Get valid fare from user
        while True:
            a_fare = input("Enter the fare of each ticket: ")
            try:
                int(a_fare)
                break
            except ValueError:
                print("Invalid input. Please enter a valid int for the fare.")
        try:

            cursor.callproc("createSchedule", [d_time, a_time, t_left, r_id, a_id, a_fare])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print("An error occurred while creating the schedule: ", e)
        # print("New Schedule created succesfully!!!")

    except Exception as e:
        print("An error occurred while creating the schedule: ", e)


def updateSchedule(mydb):
    try:
        cursor= mydb.cursor()
        try:
            cursor.callproc("getAllSchedules")
            rows = cursor.fetchall()
            allSchedules = []
            for row in rows:
                allSchedules.append(row[0])
            print(allSchedules)
            s_id = input("Enter the schedule you want to update: ")
            while(True):
                if  int(s_id) not in allSchedules:
                    print("Invalid schedule ID. Please enter a valid schedule ID.")
                    s_id = input("Enter the schedule you want to update: ")
                else:
                    break
            while (True):
                try:
                    dept_time = input("Enter the new departure time in YYYY-MM-DD HH:MM:SS format: ")
                    datetime.datetime.strptime(dept_time, '%Y-%m-%d %H:%M:%S')
                    break
                except ValueError:
                    print("Invalid arrival time format. Please enter the time in the format specified.")

            while(True):
                try:
                    arr_time = input("Enter the new arrival time in YYYY-MM-DD HH:MM:SS format: ")
                    datetime.datetime.strptime(arr_time, '%Y-%m-%d %H:%M:%S')
                    break
                except ValueError:
                    print("Invalid arrival time format. Please enter the time in the format specified.")

            cursor.callproc("updateSchedule", [s_id, dept_time, arr_time])
            mydb.commit()
            cursor.close()
            print("Schedule Updated")
        except Exception as e:
            print("An error occurred while updating the schedule: ", e)
    except Exception as e:
        print("An error occurred while updating the schedule: ", e)


def getAllDetails(mydb):
    try:
        cursor= mydb.cursor()
        try:
            cursor.callproc("getAllSchedules")
            rows = cursor.fetchall()
            allSchedules = []
            for row in rows:
                allSchedules.append(row[0])
            print(allSchedules)
            s_id = input("Enter the schedule you want to update: ")
            while(True):
                if  int(s_id) not in allSchedules:
                    print("Invalid schedule ID. Please enter a valid schedule ID.")
                    s_id = input("Enter the schedule you want to update: ")
                else:
                    break
            cursor.callproc("getAllScheduleDetails",[s_id])
            columns = [desc[0] for desc in cursor.description]
            table = PrettyTable(columns)
            rows = cursor.fetchall()
            cursor.close()
            for row in rows:
                table.add_row(row)
            print(table)

        except Exception as e:
            print("An error occurred while fetching the schedule: ", e)
    except Exception as e:
        print("An error occurred while fetching the schedule: ", e)




def staff(mydb):
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    while(True):
    # check if the email and password are correct and belong to staff
        try:
            cursor = mydb.cursor()
            cursor.execute("SELECT * FROM ground_staff WHERE employee_email = %s AND employee_password = %s",
                       (email, password))
            result = cursor.fetchone()
            cursor.close()
            if (result):
                print("Login Succesful")
                print("Welcome to the staff dashboard!.What would you like to do?")
                print("1.Search a particular passenger--->1")
                print("2.Find all bookings of a particular passenger----> 2")
                print("3.Find all passengers in a particular flight---->3")
                print("4.Add New Aircraft details---->4")
                print("5.Delete a particular schedule----> 5")
                print("6.Create a particular schedule----> 6")
                print("7.Update a particular schedule----> 7")
                print("8. Get all details of the flight ---->8")
                print("9.Logout ---->9")
                newinp = input("Please Enter your choice:")
                if newinp.lower() == "1":
                    searchEmployee(mydb)

                elif newinp.lower() == "2":
                    booksearch(mydb)

                elif newinp.lower() == "3":
                    flightSearch(mydb)
                elif newinp.lower() == "4":
                    addAircraft(mydb)
                elif newinp.lower()=="5":
                    deleteSchedule(mydb)
                elif newinp.lower() == "6":
                    createSchedule(mydb)
                elif newinp.lower() == "7":
                    updateSchedule(mydb)
                elif newinp.lower() == "8":
                    getAllDetails(mydb)
                elif newinp.lower() == "9":
                    print("STAFF LOGOUT SUCCESSFUL!LOGIN AGAIN TO CONTINUE")
                    break
                else:
                    print("Not a valid option")
                    newinp = input("Please Enter your choice:")
            else:
                print("Sorry the given credentials don't match")
                break
        except Exception as e:
            print("An error occurred while logging in as staff: ", e)


def register(mydb):
        name = input("Enter your name: ")
        while (True):
            if name.isalpha():
                break
            else:
                print("Invalid Name: e")
                name = input("Enter your name: ")

        email = input("Enter your email (should end with @gmail.com only): ")

        while(True):
            if not email.endswith("@gmail.com"):
              print("Invalid email format. Email should end with '@gmail.com'.")
              email = input("Enter your email (should end with @gmail.com only): ")
            else:
                break

        password = input("Enter your password (must be atleast 4 character): ")
        while (True):
            if len(password) < 4:
                print("Password should be at least 4 characters long.")
                password = input("Enter your password (must be atleast 4 character): ")
            else:
                break

        dob = input("Enter your date of birth in the format YYYY-MM-DD")
        while(True):
            if time.strptime(dob, "%Y-%m-%d"):
                break
            else:
                print("Entered date in wrong format")
                dob = input("Enter your date of birth in the format YYYY-MM-DD")


        city = input("Enter your city: ")
        while (True):
            if not city.isalpha():
                print("Invalid Name.")
                city = input("Enter your city: ")
            else:
                break

    # insert the new user into the database
        try:
            cursor = mydb.cursor()
            cursor.callproc("createNewUser", [name, email, password, dob, city])
            mydb.commit()
            print("Registration successful!")
            cursor.close()
        except Exception as e:
            print("An error occurred while registering the user: ", e)

def addAircraft(mydb):
    model_id = input("Enter model ID: ")
    model_name = input("Enter model Name: ")
    airlines_id = input("Enter airlines ID: ")
    airlines_name = input("Enter airlines Name: ")
    aircraft_id = input("Enter aircraft ID: ")
    aircraft_name = input("Enter aircraft name: ")
    capacity = input("Enter capacity: ")
    start_date = input("Enter start date (YYYY-MM-DD): ")

 # Call the staffEntry stored procedure with the collected inputs
    try:
        cursor = mydb.cursor()
        cursor.callproc("staffEntry", [model_id,model_name, airlines_id,airlines_name, aircraft_id, aircraft_name, capacity, start_date])
        mydb.commit()
        cursor.close()
        print("New Aircraft details added successfully!")
    except Exception as e:
        print("An error occurred while entering the new aircraft data by calling procedure staffEntry : ",
                    e)



if __name__ == '__main__':
    main()

# See PyCharm help at https://www.jetbrains.com/help/pycharm/