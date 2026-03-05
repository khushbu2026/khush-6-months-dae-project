# starting with a welcome message 
print("welcome to ECOSTYLE sustainable fashion")

# tell the user to do move to next step
print("select one from each catergory")

#ask the user to select from the option 1#occasion(party,casual.wedding)
occasion=input("please enter occasion( 'Wedding', 'Party', 'Casual':")

#if the user is not selecting the given options in occasion show an error
if  occasion != 'Wedding' and occasion != 'party' and occasion != 'casual':
    print("Error!! please enter Wedding, Party or Casual")

    different_event = input("Did user enter different event? (Yes/No): ")

#if the occassion is correct,continue
#select weather (hot,mild, cold)
else:
     weather = input("Please enter the weather (Hot, Cold, Mild): ")

 #if the user is not selecting the given option in weather show an error

     if weather != 'hot'and weather !=  'cold'and weather != 'mild':
      print ("Error!! please enter hot,coldor mild") 
    #Check the user input
     different_weather = input("Did user enter different weather? (Yes/No): ")

     #if the weather is correct,continue
     fabric = input("Please enter the fabric (Cotton, Silk, Jute): ")

  #if the user is not selecting the given option in fabric show an error
if fabric !='cotton' and fabric !='silk'and fabric !='jute':
 print("Error!! please enter cotton,silk, jute")
different_fabric = input("did user enter something different? YES/NO")

  
print("Processing information of user selection...")
print("Showing suggestions...")

continue_choice = input("Would you like to continue getting more suggestions? (Yes/No): ")

if  continue_choice == "No":
    print("Thank you. See you next time")
