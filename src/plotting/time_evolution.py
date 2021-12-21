import numpy as np
from mitiq.zne import PolyFactory
import matplotlib.pyplot as plt


def plot_time_evolution(df_results):
    time_scale = df_results.time.unique()
    scale_factors = df_results.scale_factor.unique()

    result_types = {
        'Original': {'central': [], 'error': []},
        'Output': {'central': [], 'error': []},
        'Zne': {'central': [], 'error': []},
        'Output + Zne': {'central': [], 'error': []},
        'Original2': {'central': [], 'error': []},
        'Output2': {'central': [], 'error': []},
        'Zne2': {'central': [], 'error': []},
        'Output2 + Zne2': {'central': [], 'error': []},
        'GLOrig': {'central': [], 'error': []},
        'GLOut': {'central': [], 'error': []},
        'GLZne': {'central': [], 'error': []},
        'GLOut + Zne': {'central': [], 'error': []},
        'GLSq': {'central': [], 'error': []},
        'GLSqOut': {'central': [], 'error': []},
        'GLSqZne': {'central': [], 'error': []},
        'GLSqOut + Zne': {'central': [], 'error': []}
    }

    grouped_df = df_results.groupby(['time', 'scale_factor'])[['original', 'output_corrected']].agg(
        [np.mean, np.std]).reset_index()
    grouped_df2 = df_results.groupby(['time', 'scale_factor'])[['sector_2', 'sector_2_corrected']].agg(
        [np.mean, np.std]).reset_index()
    grouped_GL = df_results.groupby(['time', 'scale_factor'])[['gauss_law', 'gauss_law_corrected']].agg(
        [np.mean, np.std]).reset_index()
    grouped_GL_sq = df_results.groupby(['time', 'scale_factor'])[
        ['gauss_law_squared', 'gauss_law_squared_corrected']].agg(
        [np.mean, np.std]).reset_index()

    # print(grouped_df.head())

    no_zne_df = grouped_df[grouped_df.scale_factor == 1.0]
    result_types['Original']['central'] = no_zne_df['original']['mean'].to_numpy()
    result_types['Original']['error'] = no_zne_df['original']['std'].to_numpy()
    #
    no_zne_df2 = grouped_df2[grouped_df2.scale_factor == 1.0]
    result_types['Original2']['central'] = no_zne_df2['sector_2']['mean'].to_numpy()
    result_types['Original2']['error'] = no_zne_df2['sector_2']['std'].to_numpy()
    #
    no_zne_GL = grouped_GL[grouped_GL.scale_factor == 1.0]
    result_types['GLOrig']['central'] = no_zne_GL['gauss_law']['mean'].to_numpy()
    result_types['GLOrig']['error'] = no_zne_GL['gauss_law']['std'].to_numpy()
    #
    no_zne_GL_sq = grouped_GL_sq[grouped_GL_sq.scale_factor == 1.0]
    result_types['GLSq']['central'] = no_zne_GL_sq['gauss_law_squared']['mean'].to_numpy()
    result_types['GLSq']['error'] = no_zne_GL_sq['gauss_law_squared']['std'].to_numpy()

    # what do I do here?
    result_types['Output']['central'] = no_zne_df['output_corrected']['mean'].to_numpy()
    result_types['Output']['error'] = no_zne_df['output_corrected']['std'].to_numpy()
    result_types['Output2']['central'] = no_zne_df2['sector_2_corrected']['mean'].to_numpy()
    result_types['Output2']['error'] = no_zne_df2['sector_2_corrected']['std'].to_numpy()
    result_types['GLOut']['central'] = no_zne_GL['gauss_law_corrected']['mean'].to_numpy()
    result_types['GLOut']['error'] = no_zne_GL['gauss_law_corrected']['std'].to_numpy()
    result_types['GLSqOut']['central'] = no_zne_GL_sq['gauss_law_squared_corrected']['mean'].to_numpy()
    result_types['GLSqOut']['error'] = no_zne_GL_sq['gauss_law_squared_corrected']['std'].to_numpy()

    for time_val in time_scale:
        time_df = grouped_df[grouped_df.time == time_val]
        central_values_zne = time_df['original']['mean'].to_numpy()
        central_values_output_zne = time_df['output_corrected']['mean'].to_numpy()
        zne, zne_error, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_zne, order=2, full_output=True)
        output_zne, output_zne_error, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_output_zne,
                                                                        order=2, full_output=True)
        result_types['Zne']['central'].append(zne)
        result_types['Zne']['error'].append(zne_error)
        result_types['Output + Zne']['central'].append(output_zne)
        result_types['Output + Zne']['error'].append(output_zne_error)

        time_df2 = grouped_df2[grouped_df2.time == time_val]
        central_values_zne2 = time_df2['sector_2']['mean'].to_numpy()
        central_values_output_zne2 = time_df2['sector_2_corrected']['mean'].to_numpy()
        zne2, zne_error2, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_zne2, order=2,
                                                            full_output=True)
        output_zne2, output_zne_error2, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_output_zne2,
                                                                          order=2, full_output=True)
        result_types['Zne2']['central'].append(zne2)
        result_types['Zne2']['error'].append(zne_error2)
        result_types['Output2 + Zne2']['central'].append(output_zne2)
        result_types['Output2 + Zne2']['error'].append(output_zne_error2)

        time_GL = grouped_GL[grouped_GL.time == time_val]
        central_values_GLzne = time_GL['gauss_law']['mean'].to_numpy()
        central_values_output_GLzne = time_GL['gauss_law_corrected']['mean'].to_numpy()
        GLzne, GLzne_error, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_GLzne, order=2,
                                                              full_output=True)
        GLzneout, GLout_error, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_output_GLzne,
                                                                 order=2, full_output=True)
        result_types['GLZne']['central'].append(GLzne)
        result_types['GLZne']['error'].append(GLzne_error)
        result_types['GLOut + Zne']['central'].append(GLzneout)
        result_types['GLOut + Zne']['error'].append(GLout_error)

        time_GL_sq = grouped_GL_sq[grouped_GL_sq.time == time_val]
        central_values_GLSqzne = time_GL_sq['gauss_law_squared']['mean'].to_numpy()
        central_values_output_GLSqzne = time_GL_sq['gauss_law_squared_corrected']['mean'].to_numpy()
        GLSqzne, GLSqzne_error, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_GLSqzne, order=2,
                                                                  full_output=True)
        GLSqzneout, GLSqout_error, _, _, _ = PolyFactory.extrapolate(scale_factors, central_values_output_GLSqzne,
                                                                     order=2, full_output=True)
        result_types['GLSqZne']['central'].append(GLSqzne)
        result_types['GLSqZne']['error'].append(GLSqzne_error)
        result_types['GLSqOut + Zne']['central'].append(GLSqzneout)
        result_types['GLSqOut + Zne']['error'].append(GLSqout_error)

    # %%
    plt.rcParams.update({
        'font.size': 14,
        # 'text.usetex': True,
        # 'text.latex.preamble': r'\usepackage{amsfonts}'
    })
    # plotting some of the data (rather than all):

    fig = plt.figure(figsize=(8, 6))

    for res_name, res_vals in result_types.items():
        if res_name == "Original":
            plt.errorbar(time_scale, res_vals['central'], res_vals['error'], color='red', marker='o',
                         linestyle='dotted',
                         capsize=7, label='Original')
        if res_name == "Output":
            plt.errorbar(time_scale, res_vals['central'], res_vals['error'], color='gray', marker='o', ls='',
                         capsize=7, label='Readout')
        if res_name == "Output + Zne":
            plt.errorbar(time_scale, res_vals['central'], res_vals['error'], fmt='', color='blue', marker='s', ls='-',
                         capsize=7, label='Readout + ZNE')

    # plt.plot(time_vector, simulator_count, marker='s', linestyle='dotted',color='black', label='Simulator')
    # plt.plot(time_vector, simulator_count, '-.', color='black', label='Simulator')
    # plt.plot(time_vector_line, simulator_count_line, linestyle='dashed', color='black', label='Simulator')
    plt.ylim((-0.02, .255))
    plt.xlabel('g t ', fontsize=24)
    plt.ylabel('L(t) = p(1100)$', fontsize=24)
    plt.title('U(1) theory (square plaquette), g=2.0', fontsize=24)
    plt.text(-.215, .276, 'a.', fontsize=38, fontweight='heavy')

    plt.legend(fontsize=16)
    plt.savefig('LechoState1_u1_sqr.pdf')
