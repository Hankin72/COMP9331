



filename = 'text.txt'

message = '<{}>\t<{}>\t<{}>\n'.format(123,'hello', '你好')

with open(filename, 'w') as file_object:
    file_object.write("hello\n")
    file_object.write(message)