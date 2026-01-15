import os
import sys

# Setup directory paths to ensure scripts are accessible
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(BASE_DIR, "scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

class SwipeGenMainMenu:
    def display_banner(self):
        print("\n" + "="*75)
        print("           🚀 SWIPEGEN HR AUTOMATION SYSTEM - FULL WORKFLOW")
        print("="*75)

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

    def run_option(self, option):
        try:
            # Mapping menu choices to the required module functions
            if option == "1":
                from option1_view_shortlist import main
            elif option == "2":
                from option2_send_invites import main
            elif option == "3":
                from option3_generate_summary import main
            elif option == "4":
                from option4_update_hired import main
            elif option == "5":
                from option5_send_details_req import main
            elif option == "6":
                from option6_generate_offers import main
            elif option == "7":
                from option7_send_offer_letters import main
            elif option == "8":
                from option8_generate_certificates import main
            elif option == "9":
                from option9_send_completion import main
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

    def run(self):
        while True:
            self.display_banner()
            self.display_menu()
            try:
                choice = input("\n👉 Select workflow step (0-9): ").strip()
            except KeyboardInterrupt:
                print("\n\n⚠️ Interrupted by user. Exiting...")
                break
            
            if choice == "0":
                print("\n👋 Thank you for using SwipeGen HR System!")
                break
            
            self.run_option(choice)
            input("\n⏎ Press Enter to return to Main Menu...")

if __name__ == "__main__":
    # Ensure environment variables are loaded if needed globally
    from dotenv import load_dotenv
    load_dotenv()
    
    SwipeGenMainMenu().run()