from flask import Flask, request
from flask_restplus import Api, Resource, fields, reqparse, marshal
import pymysql
import datetime
from base64 import b64decode, b64encode


app = Flask(__name__)

authorizations={
     'basic': {
        'type': 'basic',
         'in': 'header',
          'name': 'Authorization'
     }
}
#Connect to the database
connection = pymysql.connect(host='localhost',
                             user='root',
                             password='recovery@002',
                             database='todo_db',
                             cursorclass=pymysql.cursors.DictCursor)


api = Api(version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',
    security='basic',
    authorizations=authorizations
)

ns = api.namespace('todos', description='TODO operations')
todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due_date':fields.Date(required=True, description='The date when this task should be finished',dt_format='iso8601'),
    'status':fields.String(required=True,description='The status of the task. Can take values- Not started, In progress, Finished',default='Not Started')
})
api.add_namespace(ns)

api.init_app(app)
#Model for marshal decorator indicating invalid credentials
invalid=api.model('Failed',{                    
    'message':fields.String(default='Invalid Credentials')
})


#Check if the string date_text is a valid date in iso format
def isDateValid(date_text):
    try:
        datetime.datetime.strptime(date_text, '%Y-%m-%d')
        return True
    except :
        return False


#Helper class for user operations
class UserDAO(object):
    def __init__(self):
        self.user={}
        pass

    def login(self,user):
        cursor=connection.cursor()
        sql="select * from user where username=%s"
        cursor.execute(sql,(user['username']))
        dbUser=cursor.fetchone()
        cursor.close()
        if(dbUser==None or dbUser['password']!=user['password']):
            return 0
        self.user=dbUser
        return 1

    def isAllowed(self,user,role):                              
        if(user==None):
            return {"message":"Credentials Not Provided"}, 401
        if(self.login(user)==0):                                
            return {"message":"Invalid Credentials"}, 401

        if(self.user['role']=='read' and role=='write'):        
            return {"message":"Access Restricted"},403

        return 1,200                       
            

#Helper class for operations on todo list
class TodoDAO(object):
    def __init__(self):
        pass

    def get(self, id):
        #Create a cursor for querying db
        cursor=connection.cursor()
        sql="select * from tasks where id=%s"
        cursor.execute(sql,(id))
        todo=cursor.fetchone()
        cursor.close()      #Close the cursor
        if(todo==None):     #If task doesn't exist abort
            api.abort(404, "Todo {} doesn't exist".format(id))
        return todo

    def create(self, data):
        cursor=connection.cursor()
        sql='insert into tasks(task,due_date,status) value(%s,%s,%s)'
        cursor.execute(sql,(data['task'],data['due_date'],data['status']))
        connection.commit()

        sql='select * from tasks where id=last_insert_id()'     #Get the last inserted row 
        cursor.execute(sql)
        todo=cursor.fetchone()
        cursor.close() 
        return todo

    def update(self, id, data, statusUpdate=False):           #When status update is false it updates the entire data else only the status
        cursor=connection.cursor()
        if(statusUpdate==False):
            sql='update tasks set task=%s, status=%s, due_date=%s where id=%s'
            cursor.execute(sql,(data['task'],data['status'],data['due_date'],id))
        elif(statusUpdate==True):
            sql='update tasks set status=%s where id=%s'
            cursor.execute(sql,(data,id))
        connection.commit()

        sql='select * from tasks where id=%s'     #Get the updated data with the id
        cursor.execute(sql,(id))
        todo=cursor.fetchone()
        cursor.close() 
        return todo
        return todo

    def delete(self, id):
        cursor=connection.cursor()
        sql="delete from tasks where id=%s"
        cursor.execute(sql,(id))
        cursor.close() 
        connection.commit()

    def getAll(self,due_date=None):           #Method to get all tasks from database
        #Create a cursor for querying db
        cursor=connection.cursor()
        if(due_date is not None):             #If due_date is provided select tasks with due date
            sql="select * from tasks where due_date=%s"
            cursor.execute(sql,due_date)
        else:
            sql="select * from tasks;"
            cursor.execute(sql)
        
        todos=cursor.fetchall()          #Fetch all the rows
        cursor.close()      #Close the cursor
        return todos

    #Selects tasks that are overdue
    def getOverdue(self):       
        cursor=connection.cursor()
        sql="select * from tasks where due_date < (select curdate()) and status<>'Finished';"  #Checks if the tasks due_date is greater than current date
        cursor.execute(sql)
        todos=cursor.fetchall()          
        cursor.close()     
        return todos

    #Selects tasks that are Finished
    def getFinished(self):       
        cursor=connection.cursor()
        sql="select * from tasks where status='Finished';"  #Checks if the tasks due_date is greater than current date
        cursor.execute(sql)
        todos=cursor.fetchall()          
        cursor.close()     
        return todos



DAO = TodoDAO()
userDAO=UserDAO()


@ns.route('/')
@ns.response(code=401, model=invalid, description='Invalid Credentials')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.response(code=200, model=todo, description='Success')
    def get(self):
        '''List all tasks'''
        status=userDAO.isAllowed(request.authorization,'read')
        if(status[1]!=200):
            return status

        return marshal(DAO.getAll(), todo), 200


    @ns.doc('create_todo')
    @ns.expect(todo)            #Post request expects a todo JSON object
    @ns.response(code=201, model=todo, description='Success')
    @ns.response(code=403, model=invalid, description='Access Restricted')
    def post(self): 
        '''Create a new task'''
        data=api.payload 
        status=userDAO.isAllowed(request.authorization,'write')
        if(status[1]!=200):
            return status
        
        if(data['status'] not in ['Finished','Not Started','In Progress']):    #If status doesn't match expected value   
            return {"message":"Invalid status value provided"}, 422
       
        if(not isDateValid(data['due_date'])):           #If date provided is not a valid date
            return {"message":"Invalid date value provided"}, 422

        return marshal(DAO.create(api.payload),todo), 201

#Parser for due date 
dateParser=reqparse.RequestParser()
dateParser.add_argument('due_date',type=str,required=True,help='The Due date',location='args')

#Route and resource for fetching todo list by due date
@ns.route('/due',methods=['GET'])
class TodoListDue(Resource):
    
    @ns.doc('list_todos by due date')
    @ns.expect(dateParser)
    @ns.response(code=200, model=todo, description='Success')
    @ns.response(code=401, model=invalid, description='Invalid Credentials')
    def get(self):
        '''List all tasks by due_date'''
        status=userDAO.isAllowed(request.authorization,'read')      #Check if user is authorized to access
        if(status[1]!=200):
            return status

        args = dateParser.parse_args()
        date=args['due_date']
        return marshal(DAO.getAll(date),todo), 200


#Route and resource for fetching tasks from list which are overdue
@ns.route('/overdue',methods=['GET'])
class TodoListOverdue(Resource):

    @ns.doc('list_todos which are overdue')
    @ns.response(code=200, model=todo, description='Success')
    @ns.response(code=401, model=invalid, description='Invalid Credentials')
    def get(self):
        '''List all tasks that are overdue'''
        status=userDAO.isAllowed(request.authorization,'read')      #Check if user is authorized to access
        if(status[1]!=200):
            return status

        return marshal(DAO.getOverdue(),todo), 200


#Route and resource for fetching tasks from list which are finished.
@ns.route('/finished',methods=['GET'])
class TodoListOverdue(Resource):

    @ns.doc('list_todos which are finished')
    @ns.response(code=200, model=todo, description='Success')
    @ns.response(code=401, model=invalid, description='Invalid Credentials')
    def get(self):
        '''List all tasks that are finished'''
        status=userDAO.isAllowed(request.authorization,'read')      #Check if user is authorized to access
        if(status[1]!=200):
            return status

        return marshal(DAO.getFinished(),todo), 200

#Routes for single tasks
@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.response(code=200, model=todo, description='Success')
@ns.response(code=401, model=invalid, description='Invalid Credentials')
@ns.response(code=403, model=invalid, description='Access Restricted')
@ns.param('id', 'The identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
 
    def get(self, id):
        '''Fetch a given resource'''
        status=userDAO.isAllowed(request.authorization,'read')      #Check if user is authorized to access
        if(status[1]!=200):
            return status

        return marshal(DAO.get(id),todo)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        status=userDAO.isAllowed(request.authorization,'write')      #Check if user is authorized to access
        if(status[1]!=200):
            return status

        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        status=userDAO.isAllowed(request.authorization,'write')      #Check if user is authorized to access
        if(status[1]!=200):
            return status

        return marshal(DAO.update(id, api.payload),todo), 200


#Parser for TodoStatus put request formData
parser=reqparse.RequestParser()
parser.add_argument('status', type=str, help='Status of the task', location='form',required=True)

#Resource to update a task's status
@ns.route('/<int:id>/status', methods=['PUT'])
@ns.response(code=200, model=todo, description='Success')
@ns.response(code=401, model=invalid, description='Invalid Credentials')
@ns.response(404, 'Todo not found')
@ns.response(422, 'Incorrect value provided')
@ns.response(code=403, model=invalid, description='Access Restricted')
@ns.param('id', 'The identifier')
class TodoStatus(Resource):

    @ns.expect(parser)
    def put(self, id):
        '''Update the status of the given task. Can take values- 'Not Started','Finished','In progress' '''
        status=userDAO.isAllowed(request.authorization,'write')      #Check if user is authorized to access
        if(status[1]!=200):
            return status

        args = parser.parse_args()
        status=args['status']
        if(status not in ['Finished','Not Started','In Progress']):
            return {"message":"Invalid value provided"}, 422

        return marshal(DAO.update(id,args['status'],True),todo), 200

if __name__== "__main__":
    app.run(debug=True)
