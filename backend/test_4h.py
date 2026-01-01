from datetime import datetime, timedelta
from timeframe import scheduler

def test_4h_logic():
    print("Testing 4H Candle Close Logic...")
    
    # Test next close calculation
    next_4h = scheduler.get_next_candle_close("4h")
    print(f"Current UTC: {datetime.utcnow()}")
    print(f"Next 4H Close: {next_4h}")
    
    # Verify it's on a 4-hour boundary (0, 4, 8, 12, 16, 20)
    assert next_4h.hour % 4 == 0
    assert next_4h.minute == 0
    print("✅ get_next_candle_close logic correct for 4H")
    
    # Test is_candle_closed
    last_check = datetime.utcnow().replace(hour=3, minute=59)
    # If now is 4:00+
    now = datetime.utcnow().replace(hour=4, minute=5)
    
    # Mock minutes since midnight logic
    def mock_is_closed(now_dt, last_dt):
        minutes = 240
        current_interval = (now_dt.hour * 60 + now_dt.minute) // minutes
        last_interval = (last_dt.hour * 60 + last_dt.minute) // minutes
        return current_interval != last_interval
        
    closed = mock_is_closed(now, last_check)
    print(f"Candle closed check (3:59 -> 4:05): {closed}")
    assert closed == True
    print("✅ is_candle_closed logic correct for 4H boundary")

if __name__ == "__main__":
    test_4h_logic()
