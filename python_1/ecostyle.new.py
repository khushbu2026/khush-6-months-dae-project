# ECOSTYLE – Sustainable Fashion App

# Start the program
print("🌿 Welcome to ECOSTYLE – Sustainable Fashion")

# Loop to keep the program running until user exits
while True:
    # Display main menu
    print("\nMain Menu:") #\n is for next line
    print("A) Get Outfit Suggestion")
    print("B) Exit")

    # Ask user for choice
    choice = input("Enter your choice (A/B): ").strip().upper()

    # If user chooses Exit
    if choice == "B":
        print("Happy to see you next time at ECOSTYLE!")
        break  # Ends the program

    # If user chooses Outfit Suggestion
    elif choice == "A":

        # --- INPUT SECTION ---
        
        # Ask for occasion
        occasion = input("\nEnter occasion (casual / office / party): ").strip().lower()
        
        # Validate occasion input
        if occasion not in ["casual", "office", "party"]:
            print("❌ Error: Invalid occasion entered.")
            continue  # Go back to main menu

        # Ask for weather
        weather = input("Enter weather (hot / cold / mild): ").strip().lower()
        
        # Validate weather input
        if weather not in ["hot", "cold", "mild"]:
            print("❌ Error: Invalid weather entered.")
            continue

        # Ask for fabric
        fabric = input("Enter fabric (cotton / hemp / recycled / bamboo): ").strip().lower()
        
        # Validate fabric input
        if fabric not in ["cotton", "hemp", "recycled", "bamboo"]:
            print("❌ Error: Invalid fabric entered.")
            continue

        # --- PROCESSING LOGIC ---

        suggestion = "No exact match found, but try mixing sustainable styles!"

        # Matching combinations based on your logic
        if weather == "hot" and occasion == "casual":
            suggestion = "Cotton Jute Dress 🌿"

        elif weather == "mild" and occasion == "office":
            suggestion = "Recycled Fabric Jeans with Hemp Shirt 🌱"

        elif weather == "cold" and occasion == "party":
            suggestion = "Bamboo Silk Gown ✨"

        # --- OUTPUT ---
        print("\n👗 Suggested Outfit:", suggestion)

        # Ask user if they want to continue
        again = input("\nDo you want to continue shopping? (yes/no): ").strip().lower()

        if again != "yes":
            print("Thank you. See you next time at ECOSTYLE!")
            break

    else:
        # If user enters wrong menu choice
        print("❌ Invalid choice. Please select A or B.")