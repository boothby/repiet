stack = []

def psh(*X):
    for x in X:
        stack.append(x)

def pop():
    if stack:
        return stack.pop()
def pop2():
    if len(stack) > 1:
        return stack.pop(), stack.pop()
    else:
        return None, None

def rll(x, y):
    x %= y
    if not (y <= 0 or x == 0):
        z = -abs(x) + y * (x < 0)
        stack[-y:] = stack[z:] + stack[-y:z]


if __name__ == "__main__":
%%%DEFN%%%
    status = c_0_0_0_0
    while status is not None:
        status = status()
    
