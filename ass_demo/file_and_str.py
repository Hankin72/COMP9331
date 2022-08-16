file_path = './test.txt'

# r 只读
# w 写
# rb 以二进制的方式i进行读
# wb 以二进制的方式i进行写

# with open(file_path,'r') as fp:
#     for line in fp.readlines():
#         print(line)


from datetime import datetime

# import time
# with open(file_path, 'w') as fp:
#     fp.write(str(time.time()) + "\n")
#
#     fp.write("END")
abc = 1213123
print("{:.2f}".format(abc))

print("{1}{0}{1}{0}{1}".format('A', 'B'))

print("{:^10}".format('C'))
print("{:<10}".format('C'))
print("{:>10}".format('C'))

print("{}\t{}\t{}\t{}\t{}\t{}\n".format('asda','12','s','121','0','0'))


