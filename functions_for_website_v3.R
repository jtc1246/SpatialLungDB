# ================== TMP START ====================
options(scipen = 999)

unix_ms <- function(){
	  as.numeric(Sys.time())*1000
}

time_start <- unix_ms()

cat("====== Start: ", time_start, " ======\n")

# =================== TMP END =====================

### loading required packages
require(Seurat)
require(ggplot2)
require(RColorBrewer)
require(magrittr) # jtc
library(sf) # jtc

library(httpuv) # jtc
library(jsonlite) # jtc

cat("Import finished.\n")
time_import_finished <- unix_ms()
cat("====== Import took: ", time_import_finished - time_start, ", current time: ", time_import_finished - time_start, " ======\n")

### load seurat object
# change the path to the file of seurat object on the server
obj <- readRDS("./seuratObj_v3.rds")
obj2 <- readRDS("./seuratObj.rds")

cat("Reading finished.\n")
time_reading_finished <- unix_ms()
cat("====== Reading took: ", time_reading_finished - time_import_finished, ", current time: ", time_reading_finished - time_start, " ======\n")

### functions for expression page
# https://chatgpt.com/share/6543b78d-ef13-4b98-891c-06a25d3384bb
exp_func <- function(Igene,IcellType,pdf_path){ # pdf_path added by jtc
	## Igene should be string containing at least one gene, such as "COL1A1","CD68"
	## IcellType should be string containing at least one cell type, such as "1:Macro","2:Fibro"
	exp_func_start <- unix_ms()
	cat("====== exp_func start: ", exp_func_start - time_start, " ======\n")
	if(is.null(Igene)){
		cat("Please input at least one gene!")
	}else if(is.null(IcellType)){
		cat("Please select the cell type!")
	}else if(length(strsplit(Igene, split = ',')[[1]]) == 1 & !is.null(IcellType)){ 			
		col <- c("#66C5CC","#F89C74","#DCB0F2","#87C55F","#2F8AC4","#764E9F", "#DFFF00",
                     "#0B775E","#9A8822","#7fcdbb","#dd1c77","#4D61C6","#0CD33F", "#696969" )

		p0 <- DimPlot(obj,reduction = "umap",label = F,label.size = 6,cols = col,label.color="black",pt.size = 1,alpha = 0.8,group.by = "cluV7")+
            guides(color = guide_legend(override.aes = list(size=8), ncol=1) )+
            scale_color_manual( values = col, labels = c("0:LC-1","1:Macro","2:Fibro","3:SMC","4:Endo","5:AT2","6:Mono","7:Plasma","8:RBC", "9:LC-2","10:AT1","11:Basal","12:Nutrophil","13:Unknown") )+
            theme( plot.title = element_blank(),legend.position = c(0.8,0.5),legend.text = element_text(face = "bold", color="Black", size=18,family = "serif") )
        p0 <- LabelClusters(p0, id = "cluV7", fontface = "bold",color="Black", size=8,family = "serif")

		this_subset = subset(obj,subset = cluV8 %in% strsplit(IcellType, split = ',')[[1]])	
		subset_finished <- unix_ms()
		cat("====== subset time: ", subset_finished - exp_func_start, ", time from function start: ", subset_finished - exp_func_start, " ======\n")		  
		p1 <- VlnPlot(this_subset, features = strsplit(Igene, split = ',')[[1]], pt.size = 0.1, group.by = "cluV8", split.by = "group")+ylab("Normalized Expression")+xlab(NULL) + theme(legend.position = 'top')
        p1_violin_finished <- unix_ms()
		cat("====== p1 violin plot: ", p1_violin_finished - subset_finished, ", time from function start: ", p1_violin_finished - exp_func_start, " ======\n")
		p1 <- p1 + geom_jitter(mapping = aes(color = split), data = p1$data, position = position_jitterdodge(jitter.width = 0.4, dodge.width = 0.9))+
            guides(fill = guide_legend(override.aes = list(size=4), nrow=1) ,color="none")+
            scale_fill_manual(values = c('#FFC312','#C4E538','#12CBC4','#FDA7DF','#ED4C67',
                                         '#F79F1F','#A3CB38','#1289A7','#D980FA','#B53471',
                                         '#EE5A24','#009432','#0652DD','#9980FA','#833471',
                                         '#EA2027','#006266','#1B1464','#5758BB','#6F1E51',
                                         '#40407a','#706fd3' ))+
            scale_color_manual(values = c('#FFC312','#C4E538','#12CBC4','#FDA7DF','#ED4C67',
                                          '#F79F1F','#A3CB38','#1289A7','#D980FA','#B53471',
                                          '#EE5A24','#009432','#0652DD','#9980FA','#833471',
                                          '#EA2027','#006266','#1B1464','#5758BB','#6F1E51',
                                          '#40407a','#706fd3'))  +
			scale_x_discrete(expand = c(0, 0))+
			scale_fill_hue(breaks=c("H","COE","CO"),labels=c("non-COVID","COVID-E","COVID-A"))+
            theme( plot.title = element_blank(),legend.position = "top",legend.text = element_text(color="Black", size=10,family = "serif"),
                   axis.text.x = element_text(face = "bold",color="Black", size=18,family = "serif",angle = 0,hjust = 0.5),
                   axis.title.y = element_text(face = "bold",color="Black", size=12,family = "serif",angle = 90) )

        p1_finished <- unix_ms()
		cat("====== p1 second step: ", p1_finished - p1_violin_finished, ", time from function start: ", p1_finished - exp_func_start, " ======\n")
        
		p2 <- VlnPlot(this_subset, features = strsplit(Igene, split = ',')[[1]], pt.size = 0.1, group.by = "cluV8", split.by = "patient2",alpha = 0.1)+ylab("Normalized Expression")+xlab(NULL) + theme(legend.position = 'top')
        p2_violin_finished <- unix_ms()
		cat("====== p2 violin plot: ", p2_violin_finished - p1_finished, ", time from function start: ", p2_violin_finished - exp_func_start, " ======\n")
		p2 <- p2 + geom_jitter(mapping = aes(color = split), data = p2$data, position = position_jitterdodge(jitter.width = 0.4, dodge.width = 0.9))+
            guides(fill = guide_legend(override.aes = list(size=4), nrow=2) ,color="none")+
            scale_fill_manual(values = c('#FFC312','#C4E538','#12CBC4','#FDA7DF','#ED4C67',
                                         '#F79F1F','#A3CB38','#1289A7','#D980FA','#B53471',
                                         '#EE5A24','#009432','#0652DD','#9980FA','#833471',
                                         '#EA2027','#006266','#1B1464','#5758BB','#6F1E51',
                                         '#40407a','#706fd3' ))+
            scale_color_manual(values = c('#FFC312','#C4E538','#12CBC4','#FDA7DF','#ED4C67',
                                          '#F79F1F','#A3CB38','#1289A7','#D980FA','#B53471',
                                          '#EE5A24','#009432','#0652DD','#9980FA','#833471',
                                          '#EA2027','#006266','#1B1464','#5758BB','#6F1E51',
                                          '#40407a','#706fd3'))  +
			scale_x_discrete(expand = c(0, 0))+
            theme( plot.title = element_blank(),legend.position = "top",legend.text = element_text(color="Black", size=10,family = "serif"),
                   axis.text.x = element_text(face = "bold",color="Black", size=18,family = "serif",angle = 0,hjust = 0.5),
                   axis.title.y = element_text(face = "bold",color="Black", size=12,family = "serif",angle = 90) )

		p2_finished <- unix_ms()
		cat("====== p2 second step: ", p2_finished - p2_violin_finished, ", time from function start: ", p2_finished - exp_func_start, " ======\n")
        combined_plot <- p0|p1/p2 # jtc
		combined_plot_finished <- unix_ms()
		cat("====== combine plots: ", combined_plot_finished - p2_finished, ", time from function start: ", combined_plot_finished - exp_func_start, " ======\n")
		# print(combined_plot) # jtc
		ggsave(filename = pdf_path, plot=combined_plot, width=25, height=10); # jtc
		pdf_saved_time <- unix_ms()
		cat("====== Time to save pdf: ", pdf_saved_time - combined_plot_finished, ", time from function start: ", pdf_saved_time - exp_func_start, " ======\n")
	}else if(length(strsplit(Igene, split = ',')[[1]]) > 1 & !is.null(IcellType)){ 
		col <- c("#66C5CC","#F89C74","#DCB0F2","#87C55F","#2F8AC4","#764E9F", "#DFFF00",
                     "#0B775E","#9A8822","#7fcdbb","#dd1c77","#4D61C6","#0CD33F", "#696969" )
		cat("before p0\n")
		p0 <- DimPlot(obj,reduction = "umap",label = F,label.size = 6,cols = col,label.color="black",pt.size = 1,alpha = 0.8,group.by = "cluV7")+
			guides(color = guide_legend(override.aes = list(size=8), ncol=1) )+
			scale_color_manual( values = col, labels = c("0:LC-1","1:Macro","2:Fibro","3:SMC","4:Endo","5:AT2","6:Mono","7:Plasma","8:RBC", "9:LC-2","10:AT1","11:Basal","12:Nutrophil","13:Unknown") )+
			theme( plot.title = element_blank(),legend.position = c(0.8,0.5),legend.text = element_text(face = "bold", color="Black", size=18,family = "serif") )
        cat("inside p0\n")
		p0 <- LabelClusters(p0, id = "cluV7", fontface = "bold",color="Black", size=8,family = "serif")
		cat("p0 finished")

		this_subset = subset(obj,subset = cluV8 %in% strsplit(IcellType, split = ',')[[1]])
		subset_finished <- unix_ms()
		cat("====== subset time: ", subset_finished - exp_func_start, ", time from function start: ", subset_finished - exp_func_start, " ======\n")
		p1 <- DotPlot(this_subset,features = strsplit(Igene, split = ',')[[1]], group.by = "group" )+
            scale_colour_gradient2(low = "#000000", mid = "orange", high = "red")+
            scale_size(range = c(1,10)) +
            labs(x=NULL,y=NULL,fill  = "avg.exp")+
			scale_y_discrete(breaks=c("H","COE","CO"),labels=c("non-COVID","COVID-E","COVID-A"))+
            coord_flip() +
            theme(axis.text.x = element_text(color="Black", size=8,hjust=1,vjust = 1,angle=30),
                  legend.direction ="vertical",legend.position = "right")+
            # guides(color = guide_legend(override.aes = list(size=4), ncol=1) )
            # scale_fill_discrete(name=c("pct.exp","avg.exp"))+
            guides(size=guide_legend(ncol=1,title = "pct.exp"))+
            guides(color = guide_colorbar(title = "avg.exp"))+
			theme( legend.text = element_text(color="Black", size=10,family = "serif"),
                   axis.text.x = element_text(face = "bold",color="Black", size=18,family = "serif",angle = 0,hjust = 0.5),
                   axis.text.y = element_text(face = "bold",color="Black", size=18,family = "serif",angle = 90,hjust = 0.5) )
        p1_finished <- unix_ms()
		cat("====== p1 time: ", p1_finished - subset_finished, ", time from function start: ", p1_finished - exp_func_start, " ======\n")
        # expression among group

        p2 <- DotPlot(this_subset,features = strsplit(Igene, split = ',')[[1]], group.by = "cluV8" )+
            scale_colour_gradient2(low = "#000000", mid = "orange", high = "red")+
            scale_size(range = c(1,10)) +
            labs(x=NULL,y=NULL,fill  = "avg.exp")+
            coord_flip() +
            theme(axis.text.x = element_text(color="Black", size=8,hjust=1,vjust = 1,angle=30),
                  legend.direction ="vertical",legend.position = "right")+
            # guides(color = guide_legend(override.aes = list(size=4), ncol=1) )
            # scale_fill_discrete(name=c("pct.exp","avg.exp"))+
            guides(size=guide_legend(ncol=1,title = "pct.exp"))+
            guides(color = guide_colorbar(title = "avg.exp"))+
			theme( legend.text = element_text(color="Black", size=10,family = "serif"),
                   axis.text.x = element_text(face = "bold",color="Black", size=18,family = "serif",angle = 0,hjust = 0.5),
                   axis.text.y = element_text(face = "bold",color="Black", size=18,family = "serif",angle = 90,hjust = 0.5) )
        p2_finished <- unix_ms()
		cat("====== p2 time: ", p2_finished - p1_finished, ", time from function start: ", p2_finished - exp_func_start, " ======\n")
        combined_plot <- p0|p1/p2 # jtc
		combined_plot_finished <- unix_ms()
		cat("====== combine plots: ", combined_plot_finished - p2_finished, ", time from function start: ", combined_plot_finished - exp_func_start, " ======\n")
		# print(combined_plot) # jtc
		ggsave(filename = pdf_path, plot=combined_plot, width=25, height=10); # jtc
		pdf_saved_time <- unix_ms()
		cat("====== Time to save pdf: ", pdf_saved_time - combined_plot_finished, ", time from function start: ", pdf_saved_time - exp_func_start, " ======\n")
	}

}



### basic function called by image_FOV_cellType
subset_opt <- function(object = NULL,subset,cells = NULL, idents = NULL, Update.slots = TRUE,Update.object = TRUE,...){
		
	if (Update.slots) { 
	  message("Updating object slots..")
	  object %<>% UpdateSlots()
	}

	message("Cloing object..")
	obj_subset <- object

	# sanity check - use only cell ids (no indices)
	if (all(is.integer(cells))) { 
	  cells <- Cells(obj_subset)[cells]
	}

	if (!missing(subset) || !is.null(idents)) {
	  message("Extracting cells matched to `subset` and/or `idents`")
	}

	if (class(obj_subset) == "FOV") {
	  message("object class is `FOV` ")
	  cells <- Cells(obj_subset)
	} else if (!class(obj_subset) == "FOV" && !missing(subset)) {
	  subset <- enquo(arg = subset)
	  # cells to keep in the object
	  cells <-
		WhichCells(object = obj_subset, 
				   cells = cells,
				   idents = idents,
				   expression = subset,
				   return.null = TRUE, ...)
	} else if (!class(obj_subset) == "FOV" && !is.null(idents)) {
	  cells <-
		WhichCells(object = obj_subset, 
				   cells = cells,
				   idents = idents,
				   return.null = TRUE, ...)
	} else if (is.null(cells)) {
	  cells <- Cells(obj_subset)
	}

	# added support for object class `FOV`
	if (class(obj_subset) == "FOV") {
	  message("Matching cells for object class `FOV`..")
	  cells_check <- any(obj_subset %>% Cells %in% cells)
	} else { 
	  # check if cells are present in all FOV
	  message("Matching cells in FOVs..")
	  cells_check <-
		lapply(Images(obj_subset) %>% seq, 
			   function(i) { 
				 any(obj_subset[[Images(obj_subset)[i]]][["centroids"]] %>% Cells %in% cells) 
			   }) %>% unlist
	}

	if (all(cells_check)) { 
	  message("Cell subsets are found in all FOVs!", "\n",
			  "Subsetting object..")
	  obj_subset %<>% base::subset(cells = cells, idents = idents, ...)
	} else { 
	  # if cells are present only in one or several FOVs:
	  # subset FOVs
	  fovs <- 
		lapply(Images(obj_subset) %>% seq, function(i) {
		  if (any(obj_subset[[Images(obj_subset)[i]]][["centroids"]] %>% Cells %in% cells)) {
			message("Cell subsets are found only in FOV: ", "\n", Images(obj_subset)[i])
			message("Subsetting Centroids..")
			base::subset(x = obj_subset[[Images(obj_subset)[i]]], cells = cells, idents = idents, ...)
		  }
		}) 
	  # replace subsetted FOVs, and remove FOVs with no matching cells
	  message("Removing FOVs where cells are NOT found: ", "\n", 
			  paste0(Images(object)[which(!cells_check == TRUE)], "\n"), "\n",
			  "Subsetting cells..")
	  for (i in fovs %>% seq) { obj_subset[[Images(object)[i]]] <- fovs[[i]] }  
	  
	}

	# subset final object
	obj_subset %<>% base::subset(cells = cells, ...)

	if (Update.object && !class(obj_subset) == "FOV") { 
	  message("Updating object..")
	  obj_subset %<>% UpdateSeuratObject() }

	message("Object is ready!")
	return(obj_subset)
}


### image of FOV with cell composition
# jtc: 这个应该是 image of FOV 页面 多个gene 的函数
image_FOV_cellType <- function(Islide,Ipatient,Ifov,Igene,pdf_path){ # pdf_path added by jtc
	# Islide should be one of "S7280.1"，"S7280.2","S7280.3"，"S7280.4"
	# maybe the corresponding names mentioned "slide1","slide2","slide3","slide4"
	# Ipatient should be of the ids of the 22 patients:CO01，CO03，CO05，CO02，CO07，CO12，CO19，CO16，CO20，CO21，COE01，COE04，COE02，COE06，COE05，COE07，H02，H05，H03，H08，H09，H06
	# Ifov should be one of the fov number: 1，2，3，4，5，6，7，8，9，10....112
	# Igene could be null, could be one gene, could be no more than 3 genes, such as "CD68,CD169"
	image_fov_start <- unix_ms()
	cat("====== image_FOV_cellType start: ", image_fov_start - time_start, " ======\n")
	IF.sub.test <- subset_opt(obj2, subset = slide == Islide & patient == Ipatient & fov == Ifov)
	subset_opt_finish_time <- unix_ms()
	cat("====== subset_opt took: ", subset_opt_finish_time - image_fov_start, ", time from function start: ", subset_opt_finish_time - image_fov_start, " ======\n")
	Idents(IF.sub.test) <- factor(IF.sub.test@meta.data$cluV8)
	col <- c("#66C5CC","#F89C74","#DCB0F2","#87C55F","#2F8AC4","#764E9F", "#DFFF00",
			 "#0B775E","#9A8822","#7fcdbb","#dd1c77","#4D61C6","#0CD33F", "#696969" )
	# sub by slide ID for segement
	options(future.globals.maxSize=891289600)
	seg.xmin <- min(IF.sub.test$CenterX_global_px)
	seg.xmax <- max(IF.sub.test$CenterX_global_px)
	seg.ymin <- min(IF.sub.test$CenterY_global_px)
	seg.ymax <- max(IF.sub.test$CenterY_global_px)
	cropped.coords <- Crop(IF.sub.test[[unique(IF.sub.test$slide)]], x = c(seg.xmin, seg.xmax), y = c(seg.ymin, seg.ymax), coords = "tissue")
	IF.sub.test[["zoom1"]] <- cropped.coords
	DefaultBoundary(IF.sub.test[["zoom1"]]) <- "segmentation"
	
	if(is.null(Igene)){
		g <- ImageDimPlot(IF.sub.test, fov = "zoom1", cols = col, alpha = 0.6, crop=T, axes=T, dark.background=F,
					 mols.size = 1.5, nmols = 20000, border.color = NA, coord.fixed = T,size=1,mols.alpha=1)+
			theme_bw()+ theme(panel.grid.minor = element_blank(),  panel.grid.major = element_blank() )+
			scale_fill_manual(breaks = c("0:LC-1","1:Macro","2:Fibro","3:SMC","4:Endo","5:AT2","6:Mono",      
										 "7:Plasma","8:RBC","9:LC-2","10:AT1","11:Basal","12:Nutrophil","13:Unknown"),
							  values = c("#66C5CC","#F89C74","#DCB0F2","#87C55F","#2F8AC4","#764E9F", "#DFFF00",
										 "#0B775E","#9A8822","#7fcdbb","#dd1c77","#4D61C6","#0CD33F", "#696969" ))
		print(g)
	}else if(length(strsplit(Igene, split = ',')[[1]]) == 1){ ## Igene = "KRT5"
		### this is for the only one gene, we can test the time consuming for showing on the frontpage, if too long, please search the image and show it directly
		### when search the image from resource, if the gene name contain "/", please replace it with ".", and follow the format to search it.
		g <- ImageDimPlot(IF.sub.test, fov = "zoom1", cols = col, alpha = 0.3, molecules = strsplit(Igene, split = ',')[[1]],crop=T, axes=T, dark.background=F,
						  mols.cols = "red",mols.size = 1.5, nmols = 20000, border.color = NA, coord.fixed = T,size=1,mols.alpha=1)+
			theme_bw()+ theme(panel.grid.minor = element_blank(),  panel.grid.major = element_blank() )+
			guides(fill = guide_legend(override.aes = list(alpha = 0.3)))+
			scale_fill_manual(breaks = c("0:LC-1","1:Macro","2:Fibro","3:SMC","4:Endo","5:AT2","6:Mono",      
										 "7:Plasma","8:RBC","9:LC-2","10:AT1","11:Basal","12:Nutrophil","13:Unknown"),
							  values = c("#66C5CC","#F89C74","#DCB0F2","#87C55F","#2F8AC4","#764E9F", "#DFFF00",
										 "#0B775E","#9A8822","#7fcdbb","#dd1c77","#4D61C6","#0CD33F", "#696969" ))
		print(g)
	}else if(length(strsplit(Igene, split = ',')[[1]]) > 1 & length(strsplit(Igene, split = ',')[[1]]) <= 3){ ## Igene = "KRT5,CD68"
		###  if this function consumes too much time, we can keep it running at the backend, and show it on the frontend when finished and remind user.
		enter_if_time <- unix_ms()
		cat("====== Time to process before drawing: ", enter_if_time - subset_opt_finish_time, ", time from function start: ", enter_if_time - image_fov_start, " ======\n")
		g <- ImageDimPlot(IF.sub.test, fov = "zoom1", cols = col, alpha = 0.3, molecules = strsplit(Igene, split = ',')[[1]],crop=T, axes=T, dark.background=F,
						  mols.cols = "red",mols.size = 1.5, nmols = 20000, border.color = NA, coord.fixed = T,size=1,mols.alpha=1)+
			theme_bw()+ theme(panel.grid.minor = element_blank(),  panel.grid.major = element_blank() )+
			guides(fill = guide_legend(override.aes = list(alpha = 0.3)))+
			scale_fill_manual(breaks = c("0:LC-1","1:Macro","2:Fibro","3:SMC","4:Endo","5:AT2","6:Mono",      
										 "7:Plasma","8:RBC","9:LC-2","10:AT1","11:Basal","12:Nutrophil","13:Unknown"),
							  values = c("#66C5CC","#F89C74","#DCB0F2","#87C55F","#2F8AC4","#764E9F", "#DFFF00",
										 "#0B775E","#9A8822","#7fcdbb","#dd1c77","#4D61C6","#0CD33F", "#696969" ))+
			scale_color_manual(values = c("red","purple","orange")) 
		plot_finished_time <- unix_ms()
		cat("====== Time to draw the plot: ", plot_finished_time - enter_if_time, ", time from function start: ", plot_finished_time - image_fov_start, " ======\n")

		# print(g) # jtc
		ggsave(filename = pdf_path, plot = g) # jtc
		pdf_saved_time <- unix_ms()
		cat("====== Time to save the pdf: ", pdf_saved_time - plot_finished_time, ", time from function start: ", pdf_saved_time - image_fov_start, " ======\n")
	}else{
		### too much genes will be chaos the image, we don't support for that, give remind too much genes
		cat("Please input no more than 3 genes!")
	}

}

# ======================= FOLLOWING ADDED BY JTC ========================

# cat("start\n")
# image_FOV_cellType("S7280.3","COE05",87,"INS,TOP2A,AZU1", "test2.pdf")
# cat("finished\n")

hex_to_string <- function(hex_str) {
  # 将十六进制字符串分割成每两个字符一组
  hex_split <- strsplit(hex_str, "(?<=..)", perl = TRUE)[[1]]
  # 将每个十六进制字符转换为整数，然后转换为字符
  raw_vec <- as.raw(as.hexmode(hex_split))
  # 将原始字节序列转换为字符串
  result_str <- rawToChar(raw_vec)
  return(result_str)
}


app <- list(
  call = function(req) {
    url <- req$PATH_INFO
    json_data <- hex_to_string(substr(url, 2, nchar(url)))
    data <- fromJSON(json_data)

    f <- data$f
    if(f == 1){
      cat('image_FOV_cellType', "\n")
      image_FOV_cellType(data$p1, data$p2, data$p3, data$p4, data$p6)
    }
    if(f == 2){
      cat('exp_func', "\n")
      exp_func(data$p1, data$p2, data$p6)
    }

    # 构建响应体
    response_body <- paste0("finished")

    # 返回响应
    return(list(
      status = 200L,
      headers = list(
        'Content-Length' = '8'
      ),
      body = response_body
    ))
  }
)


server <- startServer("0.0.0.0", 9020, app)
cat("Server started on http://localhost:9020\n")


while(TRUE) {
  service()
  Sys.sleep(0.001)
}

