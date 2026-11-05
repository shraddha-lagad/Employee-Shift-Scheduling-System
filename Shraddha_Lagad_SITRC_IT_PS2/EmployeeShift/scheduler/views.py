
# Import datetime to combine a date and time into one value.
# Import timedelta to add one day for overnight shifts.
from datetime import datetime, timedelta

# render() displays an HTML page.
# redirect() redirects the user to another URL.
# get_object_or_404() finds an object or returns a 404 error if not found.
from django.shortcuts import render, redirect, get_object_or_404

# messages displays success and error notifications to the user.
from django.contrib import messages

# parse_date() converts a date string into a Python date object.
# parse_time() converts a time string into a Python time object.
from django.utils.dateparse import parse_date, parse_time

# Import the Employee and Shift database models.
from .models import Employee, Shift


# --------------------------------------------------
# FUNCTION 1: CALCULATE SHIFT START AND END TIMES
# --------------------------------------------------

def get_shift_times(shift):
    # Combine the shift date and start time into a datetime.
    start = datetime.combine(shift.date, shift.start_time)

    # Initially, use the same date for the end time.
    end = datetime.combine(shift.date, shift.end_time)

    # If it is an overnight shift, the end time belongs to
    # the following day. For example, 10 PM to 6 AM.
    # The end < start check also handles shifts that cross
    # midnight when the end time is earlier than the start time.
    if shift.overnight or end < start:
        end += timedelta(days=1)

    # Return the complete start and end datetime values.
    return start, end


# --------------------------------------------------
# FUNCTION 2: MAIN PAGE
# Handles forms and displays employees and shifts.
# --------------------------------------------------

def home(request):

    # Check whether the user submitted a form.
    if request.method == "POST":

        # Identify which form was submitted using its action value.
        action = request.POST.get("action")


        # ------------------------------------------
        # ADD EMPLOYEE
        # ------------------------------------------

        if action == "employee":

            # Get the employee name and remove extra spaces.
            name = request.POST.get("name", "").strip()

            # Get the email and remove extra spaces.
            email = request.POST.get("email", "").strip()

            # Check whether the name or email is empty.
            if not name or not email:
                messages.error(
                    request, "Please enter employee name and email."
                )

            # Check whether the email already exists.
            # iexact makes the comparison case-insensitive.
            elif Employee.objects.filter(email__iexact=email).exists():
                messages.error(request, "This email already exists.")

            else:
                # Save the new employee in the database.
                Employee.objects.create(name=name, email=email)

                # Show a success notification.
                messages.success(request, "Employee added successfully.")


        # ------------------------------------------
        # DELETE EMPLOYEE
        # ------------------------------------------

        elif action == "delete_employee":

            # Find the employee using the ID submitted by the form.
            # If the employee does not exist, return a 404 error.
            employee = get_object_or_404(
                Employee, id=request.POST.get("employee_id")
            )

            # Delete the employee from the database.
            employee.delete()

            # Show a success notification.
            messages.success(request, "Employee deleted successfully.")


        # ------------------------------------------
        # CREATE SHIFT
        # ------------------------------------------

        elif action == "shift":

            # Read the date and convert it into a date object.
            date = parse_date(request.POST.get("date", ""))

            # Read the start time and convert it into a time object.
            start_time = parse_time(request.POST.get("start_time", ""))

            # Read the end time and convert it into a time object.
            end_time = parse_time(request.POST.get("end_time", ""))

            # If the overnight checkbox is selected, this becomes True.
            overnight = request.POST.get("overnight") == "on"

            # Make sure the date and both times are valid.
            if not date or not start_time or not end_time:
                messages.error(request, "Please enter valid shift details.")

            # Reject shifts whose start and end times are identical.
            elif start_time == end_time:
                messages.error(
                    request, "Start and end times cannot be the same."
                )

            # If the end time is earlier than the start time,
            # require the user to select the overnight checkbox.
            elif end_time < start_time and not overnight:
                messages.error(
                    request,
                    "Select Overnight Shift if the shift ends after midnight."
                )

            else:
                # Create and save the shift in the database.
                Shift.objects.create(
                    date=date,
                    start_time=start_time,
                    end_time=end_time,
                    overnight=overnight
                )

                # Show a success notification.
                messages.success(request, "Shift created successfully.")


        # ------------------------------------------
        # DELETE SHIFT
        # ------------------------------------------

        elif action == "delete_shift":

            # Find the shift using the submitted shift ID.
            shift = get_object_or_404(
                Shift, id=request.POST.get("shift_id")
            )

            # Delete the shift from the database.
            shift.delete()

            # Show a success notification.
            messages.success(request, "Shift deleted successfully.")


        # ------------------------------------------
        # ASSIGN ONE EMPLOYEE TO ONE SHIFT
        # ------------------------------------------

        elif action == "assign":

            # Get the selected shift ID from the form.
            shift_id = request.POST.get("shift_id")

            # Get the selected employee ID from the form.
            employee_id = request.POST.get("employee_id")

            # Check whether the user selected both values.
            if not shift_id or not employee_id:
                messages.error(request, "Select a shift and an employee.")

            else:
                # Retrieve the selected shift from the database.
                shift = get_object_or_404(Shift, id=shift_id)

                # Retrieve the selected employee from the database.
                employee = get_object_or_404(Employee, id=employee_id)

                # Check whether this shift already has an employee.
                # If it does, do not assign another employee.
                if shift.employees.exists():
                    messages.error(
                        request,
                        "This shift already has an assigned employee."
                    )

                else:
                    # Calculate the selected shift's actual start and end.
                    # This also accounts for shifts ending after midnight.
                    start1, end1 = get_shift_times(shift)

                    # Initially, assume there is no scheduling conflict.
                    conflict_found = False

                    # Get all other shifts assigned to this employee.
                    # Exclude the shift we are currently trying to assign.
                    other_shifts = Shift.objects.filter(
                        employees=employee
                    ).exclude(id=shift.id)

                    # Check each shift already assigned to the employee.
                    for other in other_shifts:

                        # Calculate the start and end of the existing shift.
                        start2, end2 = get_shift_times(other)

                        # Two shifts overlap if each starts before
                        # the other shift ends.
                        if start1 < end2 and start2 < end1:

                            # Display the date of the conflicting shift.
                            messages.error(
                                request,
                                f"{employee.name} already has an overlapping "
                                f"shift on {other.date}."
                            )

                            # Record that a conflict was found.
                            conflict_found = True

                            # Stop checking after finding a conflict.
                            break

                    # If a conflict exists, cancel the assignment.
                    if conflict_found:
                        messages.error(
                            request,
                            "Assignment cancelled because of a shift conflict."
                        )

                    else:
                        # No conflict was found, so assign the employee.
                        # This adds the employee to the shift's ManyToMany field.
                        shift.employees.add(employee)

                        # Show a success notification.
                        messages.success(
                            request, "Employee assigned successfully."
                        )

        # After processing any form, redirect to the main page.
        # This prevents the browser from resubmitting the form on refresh.
        return redirect("home")


   
    # DISPLAY EMPLOYEES AND SHIFTS
    

    # Retrieve all employees and sort them alphabetically by name.
    employees = Employee.objects.all().order_by("name")

    # Retrieve all shifts, load their assigned employees efficiently,
    # and sort the shifts by date and then start time.
    shifts = Shift.objects.prefetch_related(
        "employees"
    ).order_by("date", "start_time")

    # Send the employee and shift data to the HTML template.
    # The template uses this information to display the lists.
    return render(
        request,
        "scheduler/home.html",
        {
            "employees": employees,
            "shifts": shifts,
        }
    )
