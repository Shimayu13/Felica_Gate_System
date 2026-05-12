plt.bar(x_pos, means, yerr=stds, capsize=8, color='black', ecolor='gray')
plt.scatter([1], [means[0]], color='blue', zorder=5, s=100, label='Mean Before')
plt.scatter([2], [means[1]], color='red', zorder=5, s=100, label='Mean After')
