hlp = "Post-processing of experiments with 1D time series (Energy dataset).
       Validate lambda for each individual time series.
"

require(optparse)
require(ggplot2)
require(scmamp)
require(xtable)

# Defined order of methods
row.order = c("Mklaren", "CSI", "ICD", "Nystrom", "Arima")

# Parse input arguments
option_list = list(
  make_option(c("-i", "--input"), type="character", help="Results file (.csv)"),
  make_option(c("-o", "--output"), type="character", help="Output directory.")
);
opt_parser = OptionParser(option_list=option_list, description=hlp);
opt = parse_args(opt_parser);
in_file = opt$input
out_dir = opt$output

# Temp paths
dir.create(out_dir, showWarnings = FALSE)

# Selection of methods
alldata = read.csv(in_file, header = TRUE, stringsAsFactors = FALSE) 
methods = unique(alldata$method)

# Generate file names
alldata$file = sprintf("%s/_%s/plot_multi-%s_tsi-%d_lbd-%0.6f_rank-%d.pdf", 
                       out_dir, alldata$signal,alldata$signal, alldata$tsi, alldata$lbd, alldata$rank)

# Select best lambda
af_val = alldata[order(alldata$method, alldata$signal, alldata$tsi, alldata$mse_val),]
af_best = af_val[!duplicated(af_val[,c("method", "signal", "tsi")]),]

# Select best method for each time series and compute win percentage
af_ranking = af_best[order(af_best$signal, af_best$tsi, af_best$mse_y),]
af_top = af_ranking[!duplicated(af_ranking[,c("signal", "tsi")]),]
af_top_count = aggregate(af_top$method, 
                         by=list(method=af_top$method), 
                         function(x) length(x) / nrow(af_top))
af_top_count = af_top_count[rev(order(af_top_count$x)),]
message("Win percentage")
print(af_top_count)

# Draw a CD plot
af_best$signal.tsi = sprintf("%s.%s", af_best$signal, af_best$tsi)
combs = unique(af_best$signal.tsi)
methods = unique(af_best$method)
M = matrix(Inf, ncol=length(combs), nrow=length(methods))
row.names(M) = methods
colnames(M) = combs
for (i in 1:nrow(af_best)){
  row = af_best[i,]
  M[row$method, row$signal.tsi] = row$mse_y
}

# Store CD plot to disk
fname = file.path(out_dir, sprintf("cd_extrapolate_val.pdf"))
pdf(fname, width=8, height=5)
plotCD(t(-M), alpha=.05)
message(sprintf("Written %s", fname))
dev.off()
