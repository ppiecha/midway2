import functools


def count_calls(func):
    @functools.wraps(func)
    def wrapper_count_calls(*args, **kwargs):
        wrapper_count_calls.num_calls += 1
        print(f"Call {wrapper_count_calls.num_calls} of {func.__name__!r}")
        return func(*args, **kwargs)
    print(f"here")
    wrapper_count_calls.num_calls = 0
    return wrapper_count_calls

@count_calls
def say_whee():
    print("Whee!")

say_whee()

say_whee()


# class TestIter:
#     def __init__(self, length=4):
#         self.dct = {item: [item] for item in range(length)}
#
#     def gen(self):
#         return (item for k, v in self.dct.items() for item in v)
#
#
# test = TestIter()
# print(test.dct)
# print(list(test.gen()))
# for i in test.gen():
#     print(i)
