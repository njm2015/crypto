# number as input
# if number / 3 print fizz
# if number / 5 print buzz
# if number / 3&5 print buzz


def fizzbuzz(n):
	# if n % 3 and n % 5:
	# 	print('fizzbuzz' end='')
	# elif n % 3:
	# 	print('fizz')
	# elif n % 5:
	# 	print('buzz')
	t = ''
	if n % 3:
		t += 'fizz'
	elif n % 5:
		t += 'buzz'

	print(t)

# if __name__ == '__main__':
# 	