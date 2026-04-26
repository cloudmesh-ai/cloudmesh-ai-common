import threading
import time
from cloudmesh.ai.common.stopwatch import StopWatch

def worker(name, duration):
    timer_name = f"timer_{name}"
    StopWatch.start(timer_name)
    time.sleep(duration)
    StopWatch.stop(timer_name)
    return StopWatch.get(timer_name)

def test_stopwatch_thread_safety():
    # Start two threads with the same timer name but different durations
    # If it's not thread-safe, they will overwrite each other.
    # However, we use different timer names here to verify they are isolated.
    # To truly test thread-safety of the SAME timer name across threads:
    
    def worker_same_name(duration):
        name = "shared_timer"
        StopWatch.start(name)
        time.sleep(duration)
        StopWatch.stop(name)
        return StopWatch.get(name)

    # We need to capture the return values. Since Thread doesn't return, 
    # we'll use a list.
    results = []
    def wrapper(duration):
        results.append(worker_same_name(duration))

    t1 = threading.Thread(target=wrapper, args=(0.1,))
    t2 = threading.Thread(target=wrapper, args=(0.2,))
    
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    # If thread-local, both should have their own timing.
    # One should be ~0.1 and other ~0.2.
    # If they shared a dictionary, the second one to stop would have 
    # a weird value or they would overwrite.
    
    assert len(results) == 2
    assert any(0.1 <= r <= 0.2 for r in results)
    assert any(0.2 <= r <= 0.3 for r in results)

def test_stopwatch_timer_context_manager():
    """Tests the StopWatch.timer context manager."""
    StopWatch.clear()
    
    # 1. Test basic timing
    timer_name = "context_timer"
    with StopWatch.timer(timer_name):
        time.sleep(0.1)
    
    val = StopWatch.get(timer_name)
    assert 0.1 <= val <= 0.2, f"Timer value {val} out of expected range"

    # 2. Test timing with exception
    timer_name_err = "error_timer"
    try:
        with StopWatch.timer(timer_name_err):
            time.sleep(0.1)
            raise RuntimeError("Test Exception")
    except RuntimeError:
        pass
    
    val_err = StopWatch.get(timer_name_err)
    assert 0.1 <= val_err <= 0.2, f"Timer value {val_err} after exception out of expected range"

    # 3. Test that it's in the keys
    assert timer_name in StopWatch.keys()
    assert timer_name_err in StopWatch.keys()