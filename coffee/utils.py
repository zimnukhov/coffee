def get_time_display(seconds):
    duration_str = ''
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60

    if hours > 0:
        duration_str += str(seconds // 3600) + ':'
        if minutes < 10:
            duration_str += '0'

    return duration_str + str(minutes) + ':%02d' % (seconds % 60)
