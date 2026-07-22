from database import show_expenses,add_expense,delete_expense

while True:
    print("\n--- EXPENSE MANAGEMENT INTERFACE ---")
    print("[1] Add Expense")
    print("[2] Show Expenses")
    print("[3] Delete Expense")
    print("[4] Exit")

    userinput = input("\n>>> Select Option: ")

    if userinput == "1":
        add_expense()

    elif userinput == "2":
        show_expenses()

    elif userinput == "3":
        delete_expense()

    elif userinput == "4":
        print("Goodbye!")
        break 
    else:
        print("Invalid option! Please enter 1, 2, 3, or 4.")




