# Import necessary libraries
import os
import sys

# Setup directory paths to ensure scripts are accessible
# Get the base directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Check if the base directory is not already in the system path
if BASE_DIR not in sys.path:
    # If not, insert it at the beginning of the system path
    sys.path.insert(0, BASE_DIR)

# Define the main menu class for the HR-Automation System
class HRAutomationMainMenu:
    # Method to display the banner
    def display_banner(self):
        print("\n" + "="*75)
        print("           🚀 HR-AUTOMATION SYSTEM - FULL WORKFLOW")
        print("="*75)

    # Method to display the menu options
    def display_menu(self):
        print("\n📋 MAIN WORKFLOW OPTIONS")
        print("-" * 75)
        # Requirement 1 & 2: Shortlisting and Inviting
        print("1. 📝 View & Shortlist Candidate Registrations")
        print("2. 📧 Send Interview Invites (Resume Shortlisted)")
        
        # Requirement 3: Reporting
        print("3. 📊 Generate Recruitment Summary Report")
        
        # Requirement 4 & 5: Hiring and Offer Details
        print("4. ✅ Update Hired Candidates (Post-Interview)")
        print("5. 📩 Send 'Offer Letter Details' Required Email")
        
        # Requirement 6 & 7: Offer Letter Generation/Sending
        print("6. 📄 Generate Internship Offer Letters (PDF)")
        print("7. ✉️  Send Offer Letters (Update to 'Ongoing')")
        
        # Requirement 8 & 9: Completion Workflow
        print("8. 🎓 Generate Internship Completion Certificates")
        print("9. 🏁 Send Completion Emails (Update to 'Completed')")
        
        print("-" * 75)
        print("0. 🚪 Exit")
        print("-" * 75)

    # Method to run the selected option
    def run_option(self, option):
        try:
            # Mapping menu choices to the required module functions
            if option == "1":
                from view_shortlist import main
            elif option == "2":
                from send_invites import main
            elif option == "3":
                from generate_summary import main
            elif option == "4":
                from update_hired import main
            elif option == "5":
                from send_details_req import main
            elif option == "6":
                from generate_offers import main
            elif option == "7":
                from send_offer_letters import main
            elif option == "8":
                from generate_certificates import main
            elif option == "9":
                from send_completion import main
            else:
                print("❌ Invalid option. Please select 0-9.")
                return
            
            # Execute the imported main function
            main()
            
        except ImportError as ie:
            print(f"❌ Script module not found: {ie}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")
            import traceback
            traceback.print_exc()

    # Method to run the main menu loop
    def run(self):
        while True:
            # Display the banner and menu
            self.display_banner()
            self.display_menu()
            try:
                # Get user input for the choice
                choice = input("\n👉 Select workflow step (0-9): ").strip()
            except KeyboardInterrupt:
                # Handle keyboard interrupt to exit gracefully
                print("\n\n⚠️ Interrupted by user. Exiting...")
                break
            
            # Check if the user wants to exit
            if choice == "0":
                print("\n👋 Thank you for using HR-Automation System!")
                break
            
            # Run the selected option
            self.run_option(choice)
            # Wait for user to press Enter before returning to the main menu
            input("\n⏎ Press Enter to return to Main Menu...")

# Entry point of the script
if __name__ == "__main__":
    # Ensure environment variables are loaded if needed globally
    from dotenv import load_dotenv
    load_dotenv()
    
    # Create an instance of the HRAutomationMainMenu class and run it
    HRAutomationMainMenu().run()
