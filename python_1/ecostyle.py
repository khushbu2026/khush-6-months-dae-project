# starting with a welcome message 
print("welcome to ECOSTYLE sustainable fashion")

# tell the user to do move to next step
print("select one from each catergory")

#ask the user to select from the option 1#occasion(party,casual.wedding)
occasion=input("select occasion( 'Wedding', 'Party', 'Casual':")

#if the user is not selecting the given options in occasion show an error
while occasion != 'Wedding' and occasion != 'party' and occasion != 'casual':
    print("Error!! please enter Wedding, Party or Casual")
    occasion=input("Select occasion Wedding, Party or casual: ")