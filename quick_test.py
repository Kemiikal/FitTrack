fromappimportapp,db,User,MealTemplate

withapp.app_context():
    db.create_all()

user=User.query.filter_by(username='__test__').first()
ifnotuser:
        user=User(username='__test__',password='pw',security_question='q',security_answer='a')
db.session.add(user)
db.session.commit()
user_id=user.id

client=app.test_client()

withclient.session_transaction()assess:
        sess['user_id']=user_id


resp=client.post('/meals',data={
'name':'Test Meal',
'calories':'250',
'protein':'10',
'carbs':'30',
'fats':'5'
},follow_redirects=True)

print('POST /meals status:',resp.status_code)
ifb'Meal added'inresp.data:
        print('Meal added OK')
else:
        print('Meal add may have failed; response snippet:')
print(resp.data.decode()[:1000])


resp2=client.get('/meals')
print('GET /meals status:',resp2.status_code)
ifb'Test Meal'inresp2.data:
        print('Meal appears in list')
else:
        print('Meal not found in list; response snippet:')
print(resp2.data.decode()[:1000])
