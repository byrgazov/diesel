
from diesel.events import Waiter, WaitPool, EarlyValue, BytesWaiter


class EarlyReadyWaiter(Waiter):
    def ready_early(self):
        return True

    def process_fire(self, value):
        return 'foo'


class Who:
    """Someone who is waiting..."""


class TestBytesWaiters:
    def test_bytes_waiters_for_the_same_bytes_have_the_same_wait_id(self):
        s1 = BytesWaiter(b'asdf')
        s2 = BytesWaiter(b'asdf')
        assert s1.wait_id == s2.wait_id

    def test_bytes_waiters_for_different_bytes_have_different_wait_ids(self):
        s1 = BytesWaiter(b'asdf')
        s2 = BytesWaiter(b'jkl;')
        assert s1.wait_id != s2.wait_id


class TestWaitPoolWithEarlyReturn:
    def setup(self):
        self.pool = WaitPool()
        self.who = Who()
        self.waiter = EarlyReadyWaiter()
        self.result = self.pool.wait(self.who, self.waiter)

    def test_results_is_EarlyValue(self):
        assert isinstance(self.result, EarlyValue)
        assert self.result.val == 'foo'

    def test_waiter_wait_id_not_added_to_wait_pool(self):
        assert self.waiter.wait_id not in self.pool.waits

    def test_who_not_added_to_wait_pool(self):
        assert self.who not in self.pool.loop_refs


class TestWaitPoolWithBytesWaiter:
    def setup(self):
        self.pool = WaitPool()
        self.who = Who()
        self.wait_for = b'a bytes'
        self.result = self.pool.wait(self.who, self.wait_for)

    def test_the_waiting_entity_is_added_to_wait_pool(self):
        assert self.pool.waits[self.wait_for]
        w = self.pool.waits[self.wait_for].pop()
        assert w is self.who

    def test_BytesWaiter_added_to_wait_pool(self):
        v = self.pool.loop_refs[self.who].pop()
        assert isinstance(v, BytesWaiter)

    def test_result_is_wait_id(self):
        assert self.result == self.wait_for
