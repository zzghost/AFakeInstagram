# -*- encoding: utf-8 -*-
from ImitativeInstagram import app, db
from flask_script import Manager
import random
from ImitativeInstagram.models import User, Image, Comments
import unittest
manager = Manager(app)

def get_image_url():
    return 'http://images.nowcoder.com/head/' + str(random.randint(0, 1000)) + 't.png'

@manager.command
def init_database():
    db.drop_all()
    db.create_all()
    # create users
    for i in range(0, 100):
        db.session.add(User('User' + str(i), 'a' + str(i)))
        # 3 pics each user.
        for j in range(0, 3):
            db.session.add(Image(get_image_url(), i + 1))
            # 3 comments each pic.
            for k in range(0, 3):
                db.session.add(Comments("This is a comment: " + str(k), 1 + 3 * i + j, i + 1))
    db.session.commit()

@manager.command
def run_test():
    db.drop_all()
    db.create_all()
    tests = unittest.TestLoader().discover("./")
    unittest.TextTestRunner().run(tests)

if __name__ == '__main__':
    manager.run()