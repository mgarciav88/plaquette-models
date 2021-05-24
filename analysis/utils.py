def get_all_spin_up_state(number_links):
    if number_links == 4:
        return '00000'
    elif number_links == 3:
        return '1111'
    else:
        print("One must have square or triangular plaquette")
        return None
