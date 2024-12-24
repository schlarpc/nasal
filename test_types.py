import pytest
import subprocess
import tempfile
import textwrap
import os
import time
from data_types import Integer, Null, Array, PureString, CoersionError

def run_openvas_nasl(script):
    with tempfile.TemporaryDirectory() as tmpdir:
        sockfile = os.path.join(tmpdir, 'redis.sock')
        configfile = os.path.join(tmpdir, 'openvas.cfg')
        scriptfile = os.path.join(tmpdir, 'script.nasl')
        redis = subprocess.Popen(
            args=['redis-server', '--unixsocket', sockfile],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        while not os.path.exists(sockfile):
            time.sleep(.001)
        with open(configfile, 'w') as f:
            f.write('kb_location = {}\n'.format(sockfile))
        with open(scriptfile, 'w') as f:
            f.write(script)
            print(script)
        proc = subprocess.run(
            args=['openvas-nasl', '-X', '-c', configfile, scriptfile],
            input=script,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=True,
        )
        redis.terminate()
        return proc

def try_nasl(expression, setup):
    script = textwrap.dedent(r"""
    {setup_statements}
    display({expression});
    display('\n' + typeof({expression}));
    """).format(
        setup_statements='\n'.join(
            'x{idx} = {value};'.format(idx=idx, value=x.as_nasl()) for idx, x in enumerate(setup)
        ),
        expression=expression,
    )
    proc = run_openvas_nasl(script)
    # print(proc.stderr)
    lines = proc.stdout.rsplit('\n', 1)
    print('OpenVAS says:', lines)
    return lines

@pytest.mark.parametrize('setup,expected', [
    ([Integer(3),        Integer(1)],        Integer(4)),
    ([Integer(-2),       Integer(1)],        Integer(-1)),
    ([PureString("foo"), Integer(1)],        PureString("foo1")),
    ([Null(),            Integer(1)],        Integer(1)),
    ([Integer(1),        Null()],            Integer(1)),
    ([Integer(1),        PureString("abc")], PureString("1abc")),
    ([PureString("ab"),  PureString("dc")],  PureString("abdc")),
    ([Null(),            Null()],            Null()),
    ([Null(),            PureString("dc")],  PureString("dc")),
    ([PureString("dc"),  Null()],            PureString("dc")),
])
def test_compare_execution(setup, expected):
    assert try_nasl('x0 + x1', setup) == [str(expected), expected.__typeof__()]
    assert setup[0] + setup[1] == expected

@pytest.mark.parametrize('setup,expected', [
    ([Integer(3)],        Integer(3)),
    ([Integer(-2)],       Integer(-2)),
    ([PureString("foo")], PureString("foo")),
    ([Null()],            Null()),
    ([Array()],           Array()),
])
def test_openvas_typeof(setup, expected):
    assert try_nasl('x0', setup) == [str(expected), expected.__typeof__()]
    assert setup[0] == expected


def test_create_integer():
    assert Integer(4)._value == 4

def test_create_integer_from_decimal():
    assert Integer('25')._value == 25

def test_create_integer_from_negative_decimal():
    assert Integer('-25')._value == -25

def test_create_integer_from_decimal_bytes():
    assert Integer(b'25')._value == 25

def test_create_integer_from_zero():
    assert Integer('0')._value == 0

def test_create_integer_from_octal():
    assert Integer('017')._value == 15

def test_create_integer_from_hex():
    assert Integer('0x66')._value == 102

def test_integer_falsy():
    assert not Integer(0)

def test_integer_truthy():
    assert Integer(22)

def test_integer_inty():
    assert int(Integer(22)) == 22

def test_integer_equals():
    assert Integer('7') == Integer(7)

def test_integer_add():
    assert Integer(4) + Integer(8) == Integer(12)

def test_integer_subtract():
    assert Integer(8) - Integer(5) == Integer(3)

def test_integer_multiply():
    assert Integer(4) * Integer(5) == Integer(20)

def test_integer_divide():
    assert Integer(5) / Integer(2) == Integer(2)

def test_integer_divide_by_zero():
    assert Integer(5) / Integer(0) == Integer(0)

@pytest.mark.xfail
def test_integer_divide_negative():
    assert Integer(5) / Integer(-2) == Integer(-3)
    # TODO what happens?
    assert False

def test_integer_modulo():
    assert Integer(7) % Integer(2) == Integer(1)

def test_integer_modulo_by_zero():
    assert Integer(7) % Integer(0) == Integer(0)

@pytest.mark.xfail
def test_integer_modulo_negative_first():
    assert Integer(-7) % Integer(2) == Integer(1)
    # TODO what happens?
    assert False

@pytest.mark.xfail
def test_integer_modulo_negative_second():
    assert Integer(7) % Integer(-2) == Integer(-1)
    # TODO what happens?
    assert False

@pytest.mark.xfail
def test_integer_modulo_negative_second():
    assert Integer(-7) % Integer(-2) == Integer(-1)
    # TODO what happens?
    assert False

def test_integer_power():
    assert Integer(2) ** Integer(4) == Integer(16)

@pytest.mark.xfail
def test_integer_power_zero():
    assert Integer(2) ** Integer(0) == Integer(1)
    # TODO what happens?
    assert False

@pytest.mark.xfail
def test_integer_power_negative():
    with pytest.raises(ValueError):
        assert Integer(2) ** Integer(-1)
    # TODO what happens?
    assert False

def test_integer_preincrement():
    n = Integer(6)
    assert n.pre_increment() == Integer(7)
    assert n == Integer(7)

def test_integer_postincrement():
    n = Integer(6)
    assert n.post_increment() == Integer(6)
    assert n == Integer(7)

def test_integer_predecrement():
    n = Integer(6)
    assert n.pre_decrement() == Integer(5)
    assert n == Integer(5)

def test_integer_postdecrement():
    n = Integer(6)
    assert n.post_decrement() == Integer(6)
    assert n == Integer(5)

def test_integer_assign_add():
    n = Integer(6)
    n += 34
    assert n == Integer(40)

def test_integer_assign_subtract():
    n = Integer(6)
    n -= 34
    assert n == Integer(-28)

def test_integer_assign_multiply():
    n = Integer(6)
    n *= 3
    assert n == Integer(18)

def test_integer_assign_divide():
    n = Integer(8)
    n /= 2
    assert n == Integer(4)

def test_integer_assign_mod():
    n = Integer(8)
    n %= 3
    assert n == Integer(2)

@pytest.mark.xfail
def test_integer_assign_operation_result():
    # TODO what happens? bool(x += 1)
    assert False

@pytest.mark.xfail
def test_integer_left_left_equals():
    # TODO what happens? <<=
    assert False

@pytest.mark.xfail
def test_integer_right_right_equals():
    # TODO what happens? >>=
    assert False

@pytest.mark.xfail
def test_integer_right_right_right_equals():
    # TODO what happens? >>>=
    assert False

@pytest.mark.xfail
def test_integer_array_access():
    # TODO what happens? n[1]
    assert False




def test_null_falsy():
    assert not Null()

def test_null_no_args():
    with pytest.raises(CoersionError):
        Null(1)

def test_null_equals():
    assert Null() == Null()

def test_null_not_equals_other_truthy_type():
    assert Null() != Integer(1)

def test_null_array_conversion():
    # WTF?
    n = Null()
    assert isinstance(n, Null)
    assert not isinstance(n, Array)
    assert n[22] == Null()
    assert isinstance(n, Array)
    assert not isinstance(n, Null)

@pytest.mark.xfail
def test_null_equals_zero():
    assert Integer(0) == Null()

@pytest.mark.xfail
def test_null_equals_empty_string():
    assert PureString('') == Null()

@pytest.mark.xfail
def test_null_equals_zero_string():
    # TODO what happens?
    assert False







def test_string_truthy():
    assert PureString("ooo")

def test_string_falsy():
    assert not PureString("")

def test_string_falsy_zero():
    assert not PureString("0")

def test_string_encode_unicode():
    with pytest.raises(ValueError):
        PureString('\u2764')

def test_string_encode_ascii():
    assert PureString('2\x001')._value == b'2\x001'

def test_string_concat():
    assert PureString('a') + PureString('b') == PureString('ab')

def test_string_subtract():
    assert PureString('abcd') - PureString('bc') == PureString('ad')

@pytest.mark.xfail
def test_string_subtract_missing():
    assert PureString('abcd') - PureString('zx') == PureString('abcd')
    # TODO what happens?
    assert False

def test_string_index():
    assert PureString('abc')[1] == PureString('b')

@pytest.mark.xfail
def test_string_index_out_of_bounds():
    assert PureString('abc')[10]
    # TODO what happens?
    assert False

@pytest.mark.xfail
def test_string_index_negative():
    assert PureString('abc')[-1]
    # TODO what happens?
    assert False

@pytest.mark.xfail
def test_string_regex_match():
    assert PureString('abc').regex_match(r'aaaa')
    # TODO what happens?
    assert False

def test_string_match():
    assert PureString('bc') in PureString('abcd')

def test_string_not_match():
    assert PureString('bd') not in PureString('abcd')



def test_array_truthy():
    assert Array()


# def test_pure_string_parsing():
    # s = PureString(r'0\x000')
    # assert s == r'0\x000'
    # assert PureString(s)._value == r'0\x000'

# def test_pure_
