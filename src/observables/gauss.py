def gauss_law(counts: dict, mitigated_counts: dict, shots: int):
    obs = 0.0
    obs_corrected = 0.0
    links = [0, 0, 0, 0, 0]
    for links[0] in range(2):
        for links[1] in range(2):
            for links[2] in range(2):
                for links[3] in range(2):
                    for links[4] in range(2):
                        s = ''
                        s += str(links[0]) + str(links[1]) + str(links[2]) + str(links[3]) + str(links[4])
                        add_links = (2 * links[0] - 1) * (2 * links[1] - 1)
                        add_corrected = add_links * mitigated_counts.get(s, 0) / shots
                        obs_corrected += add_corrected
                        add = add_links * counts.get(s, 0) / shots
                        obs += add

    return obs, obs_corrected


def sector_2(gauss_key: str, counts: dict, mitigated_counts: dict, shots: int):
    sector_2_obs = counts.get(gauss_key, 0) / shots
    sector_2_obs_corrected = mitigated_counts.get(gauss_key, 0) / shots

    return sector_2_obs, sector_2_obs_corrected


def gauss_law_squared(counts: dict, mitigated_counts: dict, shots: int):
    wind = 0.0
    wind_corrected = 0.0
    links = [0, 0, 0, 0, 0]
    for links[0] in range(2):
        for links[1] in range(2):
            for links[2] in range(2):
                for links[3] in range(2):
                    for links[4] in range(2):
                        s = ''
                        s += str(links[4]) + str(links[3]) + str(links[2]) + str(links[1]) + str(links[0])
                        add_links = (((links[0] - .5) - (links[2] - .5)) ** 2)
                        add_links += (((links[2] - .5) - (links[3] - .5)) ** 2)
                        add_links += (((links[3] - .5) - (links[4] - .5)) ** 2)
                        add_links += (((links[4] - .5) - (links[0] - .5)) ** 2)
                        add_corrected = add_links * mitigated_counts.get(s, 0) / shots
                        wind_corrected += add_corrected
                        add = add_links * counts.get(s, 0) / shots
                        wind += add

    return wind, wind_corrected
