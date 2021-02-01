import subprocess
def test(calc):
    print('SEARCHING FOR ERRORS')
    det = int(subprocess.Popen('grep WAAAAAAAAAGH tempout | wc -l',shell=True,stdout=subprocess.PIPE).communicate()[0])
    if det > 0:
        return True
    else:
        return False
