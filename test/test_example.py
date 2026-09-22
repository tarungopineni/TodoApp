import pytest
def test1():
    assert 3==3
def test2():
    assert isinstance("hello",str)
    assert isinstance(True,bool)
def test3():
    assert ("hi" == "hello") is False
def test4():
    assert type("world" is str)
def test5():
    assert type(5 is int)

class Student:
    def __init__(self,first_name:str,last_name:str,major:str,years:int):
        self.first_name = first_name
        self.last_name = last_name
        self.major = major
        self.years = years

@pytest.fixture
def default_employee():
    return Student("john","Doe","cse",4)

def test_person(default_employee):
    assert default_employee.first_name == "john","first name must be john"
    assert default_employee.last_name == "Doe","last name must be Doe"
    assert default_employee.major == "cse","student must have cse degree"
    assert default_employee.years == 4