import csv
#Stores the maximum in each subject
dict={'Maths':{'name':"",'mark':0},      
            'Biology':{'name':"",'mark':0},
            'English':{'name':"",'mark':0},
            'Physics':{'name':"",'mark':0},
            'Chemistry':{'name':"",'mark':0},
            'Hindi':{'name':"",'mark':0}}

# first>=second>=thrid
first={'Name':"","total":0}     
second={'Name':"","total":0}
third={'Name':"","total":0}

with open('Student_marks_list.csv','r') as csvfile:
    #Each row is a dictionary fo student data
    for stu in csv.DictReader(csvfile):             
        for subject,topper in dict.items():
            #If student's mark in subject is greater than topper mark then change topper
            if(int(stu[subject])>topper['mark']):               
                    dict[subject]['name']=stu['Name']        
                    dict[subject]['mark']=int(stu[subject])
        tot=0
        for key in stu:
            if(key!="Name"):
                tot+=int(stu[key])

        #total> first - third=second, second=first, first=student
        if(tot>=first['total']):              
            third.update(second)
            second.update(first)
            first['Name'], first['total']=stu['Name'],tot

        #total>second - third=second, second=student
        elif(tot>=second['total']):           
            third.update(second)
            second['Name'], second['total']=stu['Name'],tot

        #total>third - third=student
        elif(tot>=third['total']):            
            third['Name'], third['total']=stu['Name'],tot

    for subject,topper in dict.items():
        print("Topper in {0} is {1}\n".format(subject,topper['name']))

    print("Best students in the class are {0}, {1}, {2}\n".format(first['Name'],second['Name'],third['Name']))

print(
"Time complexity is O(n). n - number of students.\nSince the inner loop runs a constant number of times(6 in this case) everytime running time is 6*n which is O(n).\nSince the dictionary always consists of 6 items space complexity is constant O(1).\n"
)