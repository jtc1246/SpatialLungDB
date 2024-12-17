from R_http import *
from utils import *
from mySecrets import hexToStr
from openai import OpenAI
from time import time
import json
from random import randint
from typing import Union, Literal, Tuple
from myBasics import binToBase64
from hashlib import sha256
from queue import Queue
from _thread import start_new_thread
from copy import deepcopy

__all__ = ['process_ai_chat']


PROMPT = """## 1. Introduction and Tasks

You are an AI assistant of a website called COVID-Lung CosMX. This website is for the display of some biology data, about COVID-Lung. Its main functions include the showing the image of FOV (field of vision), gene expression, enrichment, and differential expression. Now we want to add a chatting UI on the website, users can ask any questions (precisely, send message) in natural languages.

You need to fulfil the tasks through our backend functions. More specificly, if you call the functions, the user can see the result in the browser. You also need to answer user's questions related to our website's content, if you know. You can also introduce the functions of website or how to use this if user requires. You can also answer any questions not related to this website (in this case, just act as normal GPT chatting with people).

Note that all these functions are read only (i.e. will not make any changes to the server or database). It will only show a result (can be an image, a table, some numbers and texts, or anything else) to the user.

## 2. Functions
The website has the following 4 functions, as following:

1. def fov_image(patient: str, fov: int, genes: list[str] = []) -> bytes:
    '''
    show the FOV image of the specific patient and FOV, with the genes (genes optional).
    patient should start with "CO", "COE", or "H" (stand for COVID Patient, COVID Explant Patient, and Healthy), will describe later.
    genes is a list of gene names, it can be empty, but it can only have at most 3 genes. The genes list will be provided later, it is case insensitive.
    '''

2. def gene_expression(genes: list[str], cell_types: list[str]) -> bytes:
    '''
    show the gene expression with the selected cell types.
    genes range same to above, will be provided later, should have at least 1 gene, no upper limit.
    cell_types have a list of 14 cell types, which are "Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown". Should select at least 1 from these, at most 14.
    '''

3. def enrichment(pathway: str, cell_type: str): -> bytes:
    '''
    show the enrichment of the selected pathway and cell type.

    Have the following pathways:
    1. "Pro-inflammatory", have cell_type "Macrophage", "Monocyte"
    2. "Senescence", have cell_type "Endothelial cell", "Alveolar type II cell", "Alveolar type I cell", "Basal cell"
    3. "Senescence-associated secretory phenotype (SASP)", have cell_type "Endothelial cell", "Alveolar type II cell", "Alveolar type I cell", "Basal cell"
    4. "Pro-fibrotic gene set", have cell_type "Fibroblast", "Smooth muscle cell"
    5. "Anti-fibrotic gene set", have cell_type "Fibroblast", "Smooth muscle cell"

    pathway can only be selected from above, and cell_type can only be selected the values listed in that pathway.
    '''

4. differential_exp(cell_type: str, condition: str) -> bytes:
    '''
    show the differential expression of the selected cell type and condition.

    cell_type should be selected from these: "Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown".
    condition only have 2 values: "CO v.s. H", "COE v.s. H"
    '''

5. umap_cell_composition() -> bytes:
    '''
    show the umap of cell composition in spatial lung data. This is a static image, so it does not accept any parameters.
    '''

## 3. Output Format

### 3.1 General Format

You need to choose which function(s) to call, and the parameters of it, based on the user's input. And also answer user's questions.

The final result should be a json string, a list of messages.

A message is one of the following kind:

1. text: the text content shown directly to user. In json, just use the string in json.
2. function: call our python function to generate something, and show it to user. In json, use a dict with 2 keys (name and parameters)

### 3.2 the format of function calling

Each function calling is a dict, with 2 keys: name and parameters.

1. name: the name of the python function to call.
2. parameters: a list of paramenters in python function, in the order of python functions' parameter order (even just 1 parameter, it should also be a list). Optional parameters should also be provided.

### 3.3 The content in text

There are several situations:

1. If user requests to show something, and all of them are legal and in the range of available functions, just explain what you have done in the text.
2. If user sends an illegal request or can't fulfilled by our functions, tell user the problem or explain the reason.
3. If user asks a question (whether related to this website or not), answer this question.
4. If part of request is to see something (part legal, part illegal), and part to ask question, just combine these parts (tell what are done, explain illgeal parts, and answer questions)

### 3.4 Example for formats

1. ["OK. The XXX is ..."]
2. [{"name": "func_1", "parameters": [10, "string1", ["abc", "qwe"]]}, "Here is ..."]
3. [{"name": "func_1", "parameters": [10, "string1", ["abc", "qwe"]]}, {"name": "func_2", "parameters": ["text2", 4.5, {"key1": "value1", "key2": "value2"}]}, "Here is ..."]
4. ["Sorry. XXX does not have XXX, I cannot ..., please ..."]

Note that these are only the general output format for json, not specialized for the function of this website.

### 3.5 Other notes

1. It is OK to not call any functions in your response, if user doesn't request or can't fulfilled by our functions.
2. In one response, can only contain at most one text, and text must be at the last (after any function callings).
3. Must contain text part, even if user just requires to see something and there is no problems, you should also tell what you have done in text.
4. This is a chatting mode, so you need to rememebr user's previous messages, and answer new questions based on the chatting history smartly.
5. Interact with the user directly, (i.e. use more you and I)

### 3.6 Examples for this website

1. Q: What are the DEGs in Macrophages?
A: [{\"name\": \"differential_exp\", \"parameters\": [\"Macrophage\", \"CO v.s. H\"]}, {\"name\": \"differential_exp\", \"parameters\": [\"Macrophage\", \"COE v.s. H\"]}, \"Here are the differentially expressed genes (DEGs) in Macrophages for both conditions 'CO v.s. H' and 'COE v.s. H'.\"]
2. Q: How about the inflammation in macrophage of COVID lung?
A: [{\"name\": \"enrichment\", \"parameters\": [\"Pro-inflammatory\", \"Macrophage\"]}, \"Here is the enrichment of the Pro-inflammatory pathway in Macrophage.\"]
3, Q: How about the markers’ expression of macrophage?
A: [{\"name\": \"gene_expression\", \"parameters\": [[\"CD68\", \"CD163\"], [\"Macrophage\"]]}, \"Here is the gene expression of CD68 and CD163 in Macrophage.\"]

## 4. Our Database

### 4.1 Patients and FOV

CO01: 19-36, S1
CO02: 73-90, S1
CO03: 1-18, S1
CO05: 55-72, S1
CO07: 55-72, 109-112, S2
CO12: 91-108, S2
CO16: 67-84, S3
CO19: 1-18, 103-108, S3
CO20: 1-18, S4
CO21: 55-72, S4
COE01: 91-108, S1
COE02: 73-90, S2
COE04: 37-54, S2
COE05: 85-102, S3
COE06: 19-30, S3
COE07: 37-54, S4
H02: 37-54, S1
H03: 19-36, S2
H05: 1-18, S2
H06: 19-36, S4
H08: 31-48, S3
H09: 49-66, S3

The S1, S2, S3, S4 corresponds to the slides. Although this is not required in the function, you need to be able to show image if user onlt use slide number and FOV. For example, if user want to see S2 with FOV 40, you should use COE04 40. The number range include both sides.

### 4.2 Genes

We have these 958 genes (used in fov_image and gene_expression):

AATK, ABL1, ABL2, ACACB, ACE, ACKR1, ACKR3, ACKR4, ACTA2, ACTG2, ACVR1, ACVR1B, ACVR2A, ACVRL1, ADGRA2, ADGRA3, ADGRE2, ADGRE5, ADGRF1, ADGRF3, ADGRF5, ADGRG1, ADGRG3, ADGRG5, ADGRG6, ADGRL1, ADGRL2, ADGRL4, ADGRV1, ADIPOQ, ADIRF, ADM2, AGER, AGR2, AHI1, AHR, AIF1, AKT1, ALCAM, ANGPT1, ANGPT2, ANGPTL1, ANKRD1, ANXA1, ANXA2, ANXA4, APOA1, APOC1, APOD, APOE, APP, AQP3, AR, AREG, ARF1, ARG1, ARHGDIB, ARID5B, ATF3, ATG10, ATG12, ATG5, ATM, ATP5F1E, ATR, AXL, AZGP1, AZU1, B2M, B3GNT7, BAG3, BAX, BBLN, BCL2, BCL2L1, BECN1, BEST1, BGN, BID, BIRC5, BMP1, BMP2, BMP3, BMP4, BMP5, BMP7, BMPR1A, BMPR2, BRCA1, BST1, BST2, BTF3, BTG1, BTK, C11orf96, C1QA, C1QB, C1QC, C5AR2, CACNA1C, CALB1, CALD1, CALM1, CALM2, CALM3, CAMP, CARMN, CASP3, CASP8, CASR, CAV1, CCL11, CCL13, CCL15, CCL18, CCL19, CCL2, CCL20, CCL21, CCL26, CCL28, CCL3/L1/L3, CCL4/L1/L2, CCL5, CCL8, CCND1, CCR1, CCR10, CCR2, CCR5, CCR7, CCRL2, CD14, CD163, CD164, CD19, CD2, CD209, CD24, CD27, CD274, CD276, CD28, CD300A, CD33, CD34, CD36, CD37, CD38, CD3D, CD3E, CD3G, CD4, CD40, CD40LG, CD44, CD47, CD48, CD52, CD53, CD55, CD58, CD59, CD5L, CD63, CD68, CD69, CD70, CD74, CD79A, CD80, CD81, CD83, CD84, CD86, CD8A, CD8B, CD9, CDH1, CDH11, CDH19, CDH5, CDKN1A, CDKN3, CEACAM1, CEACAM6, CELSR1, CELSR2, CENPF, CFD, CFLAR, CHEK1, CHEK2, CHI3L1, CIDEA, CIITA, CLCF1, CLDN4, CLEC10A, CLEC12A, CLEC14A, CLEC1A, CLEC2B, CLEC2D, CLEC4A, CLEC4D, CLEC4E, CLEC5A, CLEC7A, CLOCK, CLU, CMKLR1, CNTFR, COL11A1, COL12A1, COL14A1, COL15A1, COL16A1, COL17A1, COL18A1, COL1A1, COL1A2, COL21A1, COL27A1, COL3A1, COL4A1, COL4A2, COL4A5, COL5A1, COL5A2, COL5A3, COL6A1, COL6A2, COL6A3, COL8A1, COL9A2, COL9A3, COTL1, CPA3, CPB1, CRIP1, CRP, CRYAB, CSF1, CSF1R, CSF2, CSF2RA, CSF2RB, CSF3, CSF3R, CSHL1, CSK, CST7, CTLA4, CTNNB1, CTSG, CTSW, CUZD1, CX3CL1, CX3CR1, CXCL1/2/3, CXCL10, CXCL12, CXCL14, CXCL16, CXCL17, CXCL5, CXCL8, CXCL9, CXCR1, CXCR2, CXCR3, CXCR4, CXCR5, CXCR6, CYP1B1, CYP2U1, CYSTM1, CYTOR, DCN, DDC, DDIT3, DDR1, DDR2, DDX58, DHRS2, DLL1, DLL4, DMBT1, DNMT1, DNMT3A, DPP4, DST, DUSP1, DUSP2, DUSP4, DUSP5, DUSP6, EFNA1, EFNA4, EFNA5, EFNB1, EFNB2, EGF, EGFR, EIF5A/L1, ELANE, EMP3, ENG, ENO1, ENTPD1, EOMES, EPCAM, EPHA2, EPHA3, EPHA4, EPHA7, EPHB2, EPHB3, EPHB4, EPHB6, EPOR, ERBB2, ERBB3, ESAM, ESR1, ETS1, ETV4, ETV5, EZH2, EZR, FABP4, FABP5, FAM30A, FAS, FASLG, FASN, FAU, FCER1G, FCGBP, FCGR3A/B, FCRLA, FES, FFAR2, FFAR3, FFAR4, FGF1, FGF12, FGF13, FGF18, FGF2, FGF7, FGF9, FGFR1, FGFR2, FGFR3, FGG, FGR, FHIT, FKBP11, FKBP5, FLT1, FLT3LG, FN1, FOS, FOXF1, FOXP3, FPR1, FYB1, FYN, FZD1, FZD3, FZD4, FZD5, FZD6, FZD7, FZD8, G6PD, GADD45B, GAS6, GATA3, GC, GCG, GDF15, GLUD1, GLUL, GNLY, GPBAR1, GPER1, GPNMB, GPR183, GPX1, GPX3, GSN, GSTP1, GZMA, GZMB, GZMH, GZMK, H2AZ1, H4C3, HAVCR2, HBA1/2, HBB, HCAR2/3, HCK, HCST, HDAC1, HDAC11, HDAC3, HDAC4, HDAC5, HEY1, HGF, HIF1A, HILPDA, HLA-DPA1, HLA-DPB1, HLA-DQA1, HLA-DQB1/2, HLA-DRA, HLA-DRB, HMGB2, HMGN2, HPGDS, HSD17B2, HSP90AA1, HSP90AB1, HSP90B1, HSPA1A/B, HSPB1, HTT, IAPP, ICA1, ICAM1, ICAM2, ICAM3, ICOS, ICOSLG, IDO1, IER3, IFI27, IFI44L, IFIH1, IFIT1, IFIT3, IFITM1, IFITM3, IFNA1/13, IFNAR1, IFNAR2, IFNG, IFNGR1, IFNGR2, IFNL2/3, IGF1, IGF1R, IGF2, IGF2R, IGFBP3, IGFBP5, IGFBP6, IGFBP7, IGHA1, IGHD, IGHG1, IGHG2, IGHM, IGKC, IKZF3, IL10, IL10RA, IL10RB, IL11, IL11RA, IL12A, IL12B, IL12RB1, IL12RB2, IL13RA1, IL15, IL15RA, IL16, IL17A, IL17B, IL17D, IL17RA, IL17RB, IL17RE, IL18, IL18R1, IL1A, IL1B, IL1R1, IL1R2, IL1RAP, IL1RL1, IL1RN, IL2, IL20, IL20RA, IL22RA1, IL23A, IL24, IL27RA, IL2RA, IL2RB, IL2RG, IL32, IL33, IL34, IL36G, IL3RA, IL4R, IL6, IL6R, IL6ST, IL7, IL7R, INHA, INHBA, INHBB, INS, INSR, IRF3, IRF4, ITGA1, ITGA2, ITGA3, ITGA5, ITGA6, ITGA8, ITGA9, ITGAE, ITGAL, ITGAM, ITGAV, ITGAX, ITGB1, ITGB2, ITGB4, ITGB5, ITGB6, ITGB8, ITK, ITM2A, JAG1, JAK1, JAK2, JCHAIN, JUN, JUNB, KDR, KIT, KITLG, KLF2, KLK3, KLRB1, KLRF1, KLRK1, KRAS, KRT1, KRT10, KRT13, KRT14, KRT15, KRT16, KRT17, KRT18, KRT19, KRT20, KRT23, KRT4, KRT5, KRT6A/B/C, KRT7, KRT8, KRT80, KRT86, LAG3, LAIR1, LAMP2, LAMP3, LCN2, LDB2, LDHA, LDLR, LEFTY1, LEP, LGALS1, LGALS3, LGALS3BP, LGALS9, LGR5, LIF, LIFR, LINC01781, LINC01857, LINC02446, LMNA, LMNB1, LPAR5, LTB, LTBR, LTF, LUM, LY6D, LY75, LYN, LYZ, MAF, MALAT1, MAML2, MAP1LC3B/2, MAPK13, MAPK14, MARCO, MB, MECOM, MEG3, MERTK, MET, MFAP5, MGP, MHC I, MIF, MIR4435-2HG, MKI67, MMP1, MMP12, MMP14, MMP19, MMP2, MMP7, MMP9, MPO, MRC1, MRC2, MS4A1, MS4A4A, MS4A6A, MSMB, MSR1, MST1R, MT1X, MT2A, MTOR, MUC5AC, MX1, MXRA8, MYC, MYH11, MYH6, MYL12A, MYL4, MYL7, MYL9, MZB1, MZT2A/B, NACA, NANOG, NCR1, NDRG1, NEAT1, NELL2, NFKB1, NFKBIA, NGFR, NKG7, NLRC4, NLRC5, NLRP1, NLRP2, NLRP3, NOD2, NOSIP, NOTCH1, NOTCH2, NOTCH3, NPPC, NPR1, NPR2, NPR3, NR1H2, NR1H3, NR3C1, NRG1, NRXN1, NRXN3, NTRK2, NUSAP1, OAS1, OAS2, OAS3, OASL, OLFM4, OLR1, OSM, OSMR, P2RX5, PARP1, PCNA, PDCD1, PDCD1LG2, PDGFA, PDGFB, PDGFC, PDGFD, PDGFRA, PDGFRB, PDS5A, PECAM1, PF4/V1, PFN1, PGF, PGR, PHLDA2, PIGR, PLAC8, PLAC9, PNOC, POU5F1, PPARA, PPARD, PPARG, PPIA, PRF1, PRSS2, PRTN3, PSAP, PSCA, PSD3, PTGDR2, PTGDS, PTGES, PTGES2, PTGES3, PTGIS, PTGS1, PTGS2, PTK2, PTK6, PTPRC, PTPRCAP, PTTG1, QRFPR, RAC1, RAC2, RACK1, RAG1, RAMP1, RAMP2, RAMP3, RARA, RARB, RARG, RARRES1, RARRES2, RB1, RBM47, RBPJ, REG1A, RELA, RELT, RGCC, RGS1, RGS2, RGS5, RNF43, ROR1, RORA, RPL21, RPL22, RPL32, RPL34, RPL37, RPS4Y1, RSPO3, RUNX3, RXRA, RXRB, RYK, RYR2, S100A10, S100A2, S100A4, S100A6, S100A8, S100A9, S100B, S100P, SAA1/2, SARS-COV-2 N, SAT1, SCG5, SCGB3A1, SEC23A, SEC61G, SELENOP, SELL, SELPLG, SERPINA1, SERPINA3, SERPINB5, SERPINH1, SFN, SFTPB, SFTPC, SH3BGRL3, SIGIRR, SLC2A1, SLC40A1, SLPI, SMAD2, SMAD3, SMAD4, SMARCB1, SMO, SNAI1, SNAI2, SOD1, SOD2, SORBS1, SOSTDC1, SOX2, SOX4, SOX9, SPARCL1, SPINK1, SPOCK2, SPP1, SPRY2, SPRY4, SQSTM1, SRC, SREBF1, SRGN, SST, ST6GAL1, ST6GALNAC3, STAT1, STAT3, STAT4, STAT5A, STAT5B, STAT6, STMN1, SYK, TACSTD2, TAGLN, TAP1, TAP2, TBX21, TCAP, TCF7, TCL1A, TEK, TFEB, TGFB1, TGFB2, TGFB3, TGFBR1, TGFBR2, THBS1, THBS2, THSD4, TIE1, TIGIT, TIMP1, TLR1, TLR2, TLR3, TLR4, TLR5, TLR7, TLR8, TM4SF1, TNF, TNFAIP6, TNFRSF10A, TNFRSF10B, TNFRSF10D, TNFRSF11A, TNFRSF11B, TNFRSF12A, TNFRSF13B, TNFRSF14, TNFRSF17, TNFRSF18, TNFRSF19, TNFRSF1A, TNFRSF1B, TNFRSF21, TNFRSF4, TNFRSF9, TNFSF10, TNFSF12, TNFSF13B, TNFSF14, TNFSF15, TNFSF4, TNFSF8, TNFSF9, TNNC1, TNNT2, TNXA/B, TOP2A, TOX, TP53, TP53BP1, TPM1, TPM2, TPSAB1/B2, TPT1, TSC22D1, TSHZ2, TTN, TTR, TUBA1A, TUBB, TUBB4B, TWIST1, TWIST2, TXK, TYK2, TYMS, TYROBP, UBA52, UBE2C, UPK3A, VCAM1, VCAN, VEGFA, VEGFB, VEGFC, VEGFD, VHL, VIM, VPREB3, VSIR, VTN, VWA1, VWF, WIF1, WNT10B, WNT11, WNT3, WNT5A, WNT5B, WNT7A, WNT7B, WNT9A, XBP1, XCL1/2, XKR4, YBX3, YES1, ZFP36


## 5. User Input and Error Handling

In general, you should do best effort to match user's input (i.e. if the user's input is not precise or match our functionality that much, as long as it is clear that which one to call, you should do so). You are not allowed to interpret or execute user's input.
Answer all the questions in the context of COVID-Lung CosMX. But you are still allowed to answer completely unrelated questions.

More specificly, follow the following rules:

1. For vague or ambiguous input, try your best to match and call functions.
2. For completely illegal input, don't call the functions and tell the reason.
3. Ignore typos. For very small mistakes that can be corrected, you can call functions, and tell user the problem and what you have done.
4. For very vague or ambiguous input that can't be judged, tell user the reason and several options (if have), let user to choose.
5. Try your best to find the functions you can call and images to generate.


## 6. Output Requirements

Please output the json string directly, without any other explantion. The outest later must be list. NO any additional json layer, NO any additional key or item, NO any json property in text to user."""


JSON_FORMAT_ERR_MSG = """====== This is system message ======
ERROR: output format incorrect.

Please make sure that it satisfies the following, can make this python function to return True

def check_output(text: str):
    try:
        data = json.loads(text, strict=False)
    except:
        return False
    if (type(data) != list):
        return False
    if (len(data) == 0):
        return False
    for msg in data:
        if (type(msg) == str):
            continue
        if (type(msg) != dict):
            return False
        if (len(msg) != 2):
            return False
        if ('name' not in msg or 'parameters' not in msg):
            return False
        if (type(msg['name']) != str or type(msg['parameters']) != list):
            return False
    return True"""


LOG_PATH = '../openai_logs.txt'

# assert (sha256(PROMPT.encode('utf-8')).hexdigest() == '3cf69209e9d92a3282e01c47b3588670913f647f471badc5ae488e84dbb44884')
# print(sha256(PROMPT.encode('utf-8')).hexdigest())
# raise


client = OpenAI(api_key="xxxx")  # Your API key here

rate_limit_records = []

def decode_json(json_str:str):
    if (len(json_str) == 0):
        return False
    json_str = json_str.replace('\n', ' ')
    while json_str[0] in ' \n':
        json_str = json_str[1:]
    while json_str[-1] in ' \n':
        json_str = json_str[:-1]
    if(json_str.startswith('`')):
        json_str = json_str[7:-3]
    try:
        return json.loads(json_str, strict=False)
    except:
        return False

def within_rate_limit():
    t = time()
    for i in range(len(rate_limit_records)-1, -1, -1):
        if (t - rate_limit_records[i] > 3600):
            rate_limit_records.pop(i)
    if(len(rate_limit_records) >= 100):
        return False
    rate_limit_records.append(t)
    return True


def check_json_format(text: str) -> bool:
    data = decode_json(text)
    if (data == False):
        return False
    if (type(data) != list):
        return False
    if (len(data) == 0):
        return False
    for msg in data:
        if (type(msg) == str):
            continue
        if (type(msg) != dict):
            return False
        if (len(msg) != 2):
            return False
        if ('name' not in msg or 'parameters' not in msg):
            return False
        if (type(msg['name']) != str or type(msg['parameters']) != list):
            return False
    return True


def check_format(resp: str) -> Tuple[bool, str]:
    '''
    returns: (success, error_msg)
    '''
    json_legal = check_json_format(resp)
    if (json_legal == False):
        return (False, JSON_FORMAT_ERR_MSG)
    has_text = False  # whether has the text (str) shown to user, should include at least 1, but here 
    pass              # does not check its location and whether more than 1
    err_msg = ''
    resp = decode_json(resp)
    for msg in resp:
        if (type(msg) == str):
            has_text = True
            continue
        func_name = msg['name']
        parameters = msg['parameters']
        if (func_name not in ['fov_image', 'gene_expression', 'enrichment', 'differential_exp', 'umap_cell_composition']):
            err_msg += f'Function name "{func_name}" not found, only has: fov_image, gene_expression, enrichment, differential_exp. '
            continue
        if (func_name == 'enrichment'):
            if (len(parameters) != 2):
                err_msg += f'Function {func_name} must receive exactly 2 parameters, note that optional arguments must also be provided. '
                continue
            if (type(parameters[0]) != str):
                err_msg += f'In function {func_name}, pathway must be str. '
            if (type(parameters[1]) != str):
                err_msg += f'In function {func_name}, cell_type must be str. '
            if (type(parameters[0]) != str or type(parameters[1]) != str):
                continue
            pathway = parameters[0]
            cell_type = parameters[1]
            allowed_pathways = ['Pro-inflammatory', 'Senescence', 'Senescence-associated secretory phenotype (SASP)', 'Pro-fibrotic gene set', 'Anti-fibrotic gene set']
            pathway_loc = find_after_format(allowed_pathways, pathway)
            if (pathway_loc == -1):
                err_msg += f'In function {func_name}, pathway "{pathway}" not found, only has: "Pro-inflammatory", "Senescence", "Senescence-associated secretory phenotype (SASP)", "Pro-fibrotic gene set", "Anti-fibrotic gene set". '
                continue
            if (pathway_loc == 0):
                allowed_cell_types = ['Macrophage', 'Monocyte']
                cell_type_loc = find_after_format(allowed_cell_types, cell_type)
                if (cell_type_loc == -1):
                    err_msg += f'In function {func_name}, cell type "{cell_type}" not found, pathway "{pathway}" only has: "Fibroblast", "Smooth muscle cell". '
            elif (pathway_loc in [3, 4]):
                allowed_cell_types = ['Fibroblast', 'Smooth muscle cell']
                cell_type_loc = find_after_format(allowed_cell_types, cell_type)
                if (cell_type_loc == -1):
                    err_msg += f'In function {func_name}, cell type "{cell_type}" not found, pathway "{pathway}" only has: "Fibroblast", "Smooth muscle cell". '
            else:
                allowed_cell_types = ['Endothelial cell', 'Alveolar type II cell', 'Alveolar type I cell', 'Basal cell']
                cell_type_loc = find_after_format(allowed_cell_types, cell_type)
                if (cell_type_loc == -1):
                    err_msg += f'In function {func_name}, cell type "{cell_type}" not found, pathway "{pathway}" only has: "Endothelial cell", "Alveolar type II cell", "Alveolar type I cell", "Basal cell". '
        if (func_name == 'differential_exp'):
            if (len(parameters) != 2):
                err_msg += f'Function {func_name} must receive exactly 2 parameters, note that optional arguments must also be provided. '
                continue
            if (type(parameters[0]) != str):
                err_msg += f'In function {func_name}, cell_type must be str. '
            if (type(parameters[1]) != str):
                err_msg += f'In function {func_name}, condition must be str. '
            if (type(parameters[0]) != str or type(parameters[1]) != str):
                continue
            cell_type = parameters[0]
            condition = parameters[1]
            allowed_cell_types = ["Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown"]
            allowed_conditions = ["CO v.s. H", "COE v.s. H"]
            if (find_after_format(allowed_cell_types, cell_type) == -1):
                err_msg += f'In function {func_name}, cell type "{cell_type}" not found, only has: "Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown". '
            if (find_after_format(allowed_conditions, condition) == -1):
                err_msg += f'In function {func_name}, condition "{condition}" not found, only has: "CO v.s. H", "COE v.s. H". '
        if (func_name == 'gene_expression'):
            if (len(parameters) != 2):
                err_msg += f'Function {func_name} must receive exactly 2 parameters, note that optional arguments must also be provided. '
                continue
            if (is_list_str(parameters[0]) == False):
                err_msg += f'In function {func_name}, genes must be a list of str. '
            if (is_list_str(parameters[1]) == False):
                err_msg += f'In function {func_name}, cell_types must be a list of str. '
            if (is_list_str(parameters[0]) == False or is_list_str(parameters[1]) == False):
                continue
            if (len(parameters[0]) == 0):
                err_msg += f'In function {func_name}, genes cannot be empty. '
            if (len(parameters[1]) == 0):
                err_msg += f'In function {func_name}, cell_types cannot be empty. '
            allowed_cell_types = ["Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown"]
            for cell_type in parameters[1]:
                if (find_after_format(allowed_cell_types, cell_type) == -1):
                    err_msg += f'In function {func_name}, cell type "{cell_type}" not found, only has: "Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown". '
            for gene in parameters[0]:
                if (format_str(gene) not in GENES_AI_FORMATTED_TO_ORIGIN):
                    err_msg += f'In function {func_name}, gene "{gene}" not found. '
        if (func_name == 'fov_image'):
            if (len(parameters) != 3):
                err_msg += f'Function {func_name} must receive exactly 3 parameters, note that optional arguments must also be provided. '
                continue
            if (type(parameters[0]) != str):
                err_msg += f'In function {func_name}, patient must be str. '
            if (type(parameters[1]) != int):
                err_msg += f'In function {func_name}, fov must be int. '
            if (is_list_str(parameters[2]) == False):
                err_msg += f'In function {func_name}, cell_types must be a list of str. '
            if ((type(parameters[0]) != str) or (type(parameters[1]) != int) or (is_list_str(parameters[2]) == False)):
                continue
            if (len(parameters[2]) > 3):
                err_msg += f"In function {func_name}, genes can only have at most 3 genes. "
            patient = parameters[0]
            fov = parameters[1]
            allowed_patients = ['CO01', 'CO02', 'CO03', 'CO05', 'CO07', 'CO12', 'CO16', 'CO19', 'CO20', 'CO21'] + \
                               ['COE01', 'COE02', 'COE04', 'COE05', 'COE06', 'COE07'] + \
                               ['H02', 'H03', 'H05', 'H06', 'H08', 'H09']
            patient_loc = find_after_format(allowed_patients, patient)
            patient = allowed_patients[patient_loc]
            fov_ranges = {"CO01": ((19, 36),), "CO02": ((73, 90),), "CO03": ((1, 18),), "CO05": ((55, 72),), "CO07": ((55, 72), (109, 112)), "CO12": ((91, 108),), "CO16": ((67, 84),), "CO19": ((1, 18), (103, 108)), "CO20": ((1, 18),), "CO21": ((55, 72),), "COE01": ((91, 108),), "COE02": ((73, 90),), "COE04": ((37, 54),), "COE05": ((85, 102),), "COE06": ((19, 30),), "COE07": ((37, 54),), "H02": ((37, 54),), "H03": ((19, 36),), "H05": ((1, 18),), "H06": ((19, 36),), "H08": ((31, 48),), "H09": ((49, 66),)}
            fov_texts = {"CO01": "19-36, S1", "CO02": "73-90, S1", "CO03": "1-18, S1", "CO05": "55-72, S1", "CO07": "55-72, 109-112, S2", "CO12": "91-108, S2", "CO16": "67-84, S3", "CO19": "1-18, 103-108, S3", "CO20": "1-18, S4", "CO21": "55-72, S4", "COE01": "91-108, S1", "COE02": "73-90, S2", "COE04": "37-54, S2", "COE05": "85-102, S3", "COE06": "19-30, S3", "COE07": "37-54, S4", "H02": "37-54, S1", "H03": "19-36, S2", "H05": "1-18, S2", "H06": "19-36, S4", "H08": "31-48, S3", "H09": "49-66, S3"}
            fov_range = fov_ranges[patient]
            fov_in_range = False
            for fov_range_item in fov_range:
                if (fov >= fov_range_item[0] and fov <= fov_range_item[1]):
                    fov_in_range = True
                    break
            if (fov_in_range == False):
                err_msg += f'FOV {fov} is not in {patient}, {patient} only has: {fov_texts[patient]}. '
    if (err_msg != ''):
        err_msg = '====== This is a system message ======\nERROR: ' + err_msg + '\n\nPlease retry to fix this. You can either call the function again, or tell user the problem.'
    if (err_msg == ''):
        print('======== check_format: success.')
    else:
        print('======== check_format: failed.  \n' + err_msg)
    return (err_msg == '', err_msg)


def format_gpt_resp(resp: str) -> list:
    '''
    returns: (success, error_msg)
    '''
    results = []
    resp = decode_json(resp)
    for msg in resp:
        if (type(msg) == str):
            results.append(msg)
            continue
        func_name = msg['name']
        parameters = msg['parameters']
        current = {'name': func_name}
        if (func_name == 'enrichment'):
            pathway = parameters[0]
            cell_type = parameters[1]
            allowed_pathways = ['Pro-inflammatory', 'Senescence', 'Senescence-associated secretory phenotype (SASP)', 'Pro-fibrotic gene set', 'Anti-fibrotic gene set']
            pathway_loc = find_after_format(allowed_pathways, pathway)
            final_pathway = allowed_pathways[pathway_loc]
            if (pathway_loc == 0):
                allowed_cell_types = ['Macrophage', 'Monocyte']
            elif (pathway_loc in [3, 4]):
                allowed_cell_types = ['Fibroblast', 'Smooth muscle cell']
            else:
                allowed_cell_types = ['Endothelial cell', 'Alveolar type II cell', 'Alveolar type I cell', 'Basal cell']
            cell_type_loc = find_after_format(allowed_cell_types, cell_type)
            final_cell_type = allowed_cell_types[cell_type_loc]
            current['parameters'] = [final_pathway, final_cell_type]
            results.append(current)
            continue
        if (func_name == 'differential_exp'):
            cell_type = parameters[0]
            condition = parameters[1]
            allowed_cell_types = ["Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown"]
            allowed_conditions = ["CO v.s. H", "COE v.s. H"]
            selected_cell_type = allowed_cell_types[find_after_format(allowed_cell_types, cell_type)]
            selected_condition = allowed_conditions[find_after_format(allowed_conditions, condition)]
            current['parameters'] = [selected_cell_type, selected_condition]
            results.append(current)
            continue
        if (func_name == 'gene_expression'):
            allowed_cell_types = ["Lymphocytes1", "Macrophage", "Fibroblast", "Smooth muscle cell", "Endothelial cell", "Alveolar type II cell", "Monocyte", "Plasma cell", "Red blood cell", "Lymphocytes2", "Alveolar type I cell", "Basal cell", "Neutrophil", "Unknown"]
            final_cell_types = []
            final_genes = []
            for cell_type in parameters[1]:
                final_cell_types.append(allowed_cell_types[find_after_format(allowed_cell_types, cell_type)])
            for gene in parameters[0]:
                final_genes.append(GENES_AI_FORMATTED_TO_ORIGIN[format_str(gene)])
            final_genes = list(set(final_genes))
            current['parameters'] = [final_genes, final_cell_types]
            results.append(current)
            continue
        if (func_name == 'fov_image'):
            patient = parameters[0]
            fov = parameters[1]  # already legal
            allowed_patients = ['CO01', 'CO02', 'CO03', 'CO05', 'CO07', 'CO12', 'CO16', 'CO19', 'CO20', 'CO21'] + \
                               ['COE01', 'COE02', 'COE04', 'COE05', 'COE06', 'COE07'] + \
                               ['H02', 'H03', 'H05', 'H06', 'H08', 'H09']
            patient_loc = find_after_format(allowed_patients, patient)
            final_patient = allowed_patients[patient_loc]
            final_genes = []
            for gene in parameters[2]:
                if (format_str(gene) in GENES_AI_FORMATTED_TO_ORIGIN):
                    final_genes.append(GENES_AI_FORMATTED_TO_ORIGIN[format_str(gene)])
            final_genes = list(set(final_genes))
            current['parameters'] = [final_patient, fov, final_genes]
            results.append(current)
            continue
        if (func_name == 'umap_cell_composition'):
            current['parameters'] = []
            results.append(current)
    return results


def get_gpt_resp(history: list) -> Tuple[bool, str, str]:
    '''
    returns: (success, error_msg, response)
    
    will modify the history
    '''
    # history = deepcopy(history)
    trial = 4
    while (trial > 0):
        trial -= 1
        try:
            response = client.chat.completions.create(
                model = 'gpt-4o-2024-08-06',
                temperature=0.6,
                messages=history,
                top_p=1.0,
                max_tokens=3072
            )
            result = response.choices[0].message.content
            log_queue.put(json.dumps({'history': history, 'response': result}, ensure_ascii=False))
        except:
            # will not retry if ChatGPT API fails
            return (False, 'Failed to get the response from GPT. Please copy your input, refresh the page and try again.', '')
        success, err_msg = check_format(result)
        if (success):
            history.append({'role': 'assistant', 'content': result})
            print(f'======== GPT success after {4-trial} trials.')
            return (True, '', result)
        history.append({'role': 'assistant', 'content': result})
        history.append({'role': 'user', 'content': err_msg})
    print('======== GPT fails after 4 trials.')
    return (False, 'GPT returns illegal format after max retries. Please copy your input, refresh the page and try again.', '')


# Strategy: all the data is stored in frontend, backend does not store any data, is stateless
# In each request, frontend sends all the history (current message also in history)
# Server sends back the results (images and text), and also the full history
# History is in openai format, but not include the system message
# The messages responded from GPT has 3 types: image, text, error
# 1. Image: show the generated image: use base64 encoded, put in json
# 2. Text: put in json directly
# 3. Error: error in GPT response (unable to call functions due to illegal input), and error from R
#           this only includes the error from single function, not includes the global json format
# The frontend needs to keep the record of 2 histories: the GPT chatting history for new message,
#   and the client-side chatting history (i.e. the texts and images displayed in browser)
# For the global errors (e.g. json format error, no specific parts), do nothing, prompt the 
#   user to retry


def generate_messgae(formatted_resp: list) -> str:
    messages = []
    for msg in formatted_resp:
        if (type(msg) == str):
            messages.append({'type': 'text', 'content': msg})
            continue
        func_name = msg['name']
        if (func_name == 'enrichment'):
            pathway = msg['parameters'][0]
            cell_type = msg['parameters'][1]
            cell_type_name = {
                'Macrophage': 'macro',
                'Monocyte': 'Mono',
                'Fibroblast': 'Fibroblast',
                'Smooth muscle cell': 'SMCs',
                'Endothelial cell': 'Endo',
                'Alveolar type II cell': 'AT2',
                'Alveolar type I cell': 'AT1',
                'Basal cell': 'Basal'
            }[cell_type]
            final_pathway = ''
            if (pathway.startswith('Pro-in')):
                final_pathway = 'proinformmatory'
            elif (pathway.startswith('Pro-f')):
                final_pathway = 'pro_fibrotic'
            elif (pathway.startswith('Anti')):
                final_pathway = 'anti_fibrotic'
            elif (pathway.endswith('SP)')):
                final_pathway = 'SASP'
            elif (pathway == 'Senescence'):
                final_pathway = 'senescence'
            else:
                assert False
            file_name = f'{final_pathway}_related_genes_in_{cell_type_name}.png'
            url = f'$data-server-url$/05.enrichment/{file_name}'
            messages.append({'type': 'image', 'content': url})
            continue
        if (func_name == 'differential_exp'):
            cell_type = msg['parameters'][0]
            condition = msg['parameters'][1]
            condition = 'COE' if 'COE' in condition else 'CO'
            cell_type = {
                'Lymphocytes1': 'LC1',
                'Macrophage': 'Macro',
                'Fibroblast': 'Fibro',
                'Smooth muscle cell': 'SMC',
                'Endothelial cell': 'Endo',
                'Alveolar type II cell': 'AT2',
                'Monocyte': 'Mono',
                'Plasma cell': 'Plasma',
                'Red blood cell': 'RBC',
                'Lymphocytes2': 'LC2',
                'Alveolar type I cell': 'AT1',
                'Basal cell': 'Basal',
                'Neutrophil': 'Nutrophil',
                'Unknown': 'Unknown'
            }[cell_type]
            file_name = f'DEGs_from_{condition}_in_{cell_type}.png'
            url = f'$data-server-url$/06.diff_exp/{file_name}'
            messages.append({'type': 'image', 'content': url})
            continue
        if (func_name == 'gene_expression'):
            genes = msg['parameters'][0]
            cell_types = msg['parameters'][1]
            # ['0:LC-1', '1:Macro', '2:Fibro', '3:SMC', '4:Endo', '5:AT2', '6:Mono', '7:Plasma', '8:RBC', '9:LC-2', '10:AT1', '11:Basal', '12:Nutrophil', '13:Unknown']
            cell_type_to_short = {
                'Lymphocytes1': '0:LC-1',
                'Macrophage': '1:Macro',
                'Fibroblast': '2:Fibro',
                'Smooth muscle cell': '3:SMC',
                'Endothelial cell': '4:Endo',
                'Alveolar type II cell': '5:AT2',
                'Monocyte': '6:Mono',
                'Plasma cell': '7:Plasma',
                'Red blood cell': '8:RBC',
                'Lymphocytes2': '9:LC-2',
                'Alveolar type I cell': '10:AT1',
                'Basal cell': '11:Basal',
                'Neutrophil': '12:Nutrophil',
                'Unknown': '13:Unknown'
            }
            cell_types = [cell_type_to_short[cell_type] for cell_type in cell_types]
            cell_types = ','.join(cell_types)
            genes.sort()
            genes = ','.join(genes)
            t = str(time())
            task_id = sha256((f'{genes}_{cell_types}_{t}').encode('utf-8')).hexdigest()
            resp = gene_expression(genes, cell_types, f'./tmp/{task_id}.pdf')
            if (resp[0] == False):
                err_msg = binary_to_str(resp[1])
                messages.append({'type': 'error', 'content': err_msg})
                continue
            file_path = f'../docker/resources/04.exp_functions/tmp/{task_id}.pdf'
            png_bytes = pdf_to_png_bytes(file_path)
            png_base64 = binToBase64(png_bytes)
            png_base64 = 'data:image/png;base64,' + png_base64
            messages.append({'type': 'image', 'content': png_base64})
            continue
        if (func_name == 'fov_image'):
            # messages.append({'type': 'error', 'content': 'Currently fov_image is not implemented.'})
            # continue
            patient = msg['parameters'][0]
            fov = msg['parameters'][1]
            genes = msg['parameters'][2]
            if (len(genes) == 0):
                link = f'/02.images/{patient}/{patient}.{fov}.png'
            elif (len(genes) == 1):
                gene = genes[0].replace(' ', '@').replace('/', '.')
                link = f'/02.images/{patient}/{patient}.{fov}.{gene}.png'
            if (len(genes) <= 1):
                link = '$data-server-url$' + link
                messages.append({'type': 'image', 'content': link})
                continue
            # messages.append({'type': 'error', 'content': 'Currently fov_image with multiple genes is not implemented.'})
            genes.sort()
            genes = ','.join(genes)
            t = str(time())
            task_id = sha256((f'{patient}_{fov}_{genes}_{t}').encode('utf-8')).hexdigest()
            slide_num = SAMPLE_FOV_TO_SLIDE[(patient, fov)]
            slide = f'S7280.{slide_num}'
            resp = fov_multi(slide, patient, fov, genes, f'./tmp/{task_id}.pdf')
            if (resp[0] == False):
                err_msg = binary_to_str(resp[1])
                messages.append({'type': 'error', 'content': err_msg})
                continue
            file_path = f'../docker/resources/04.exp_functions/tmp/{task_id}.pdf'
            png_bytes = pdf_to_png_bytes(file_path)
            png_base64 = binToBase64(png_bytes)
            png_base64 = 'data:image/png;base64,' + png_base64
            messages.append({'type': 'image', 'content': png_base64})
            continue
        if (func_name == 'umap_cell_composition'):
            with open('./imgs/umap.png', 'rb') as f:
                png_bytes = f.read()
            png_base64 = binToBase64(png_bytes)
            png_base64 = 'data:image/png;base64,' + png_base64
            messages.append({'type': 'image', 'content': png_base64})
    return messages
            

def process_ai_chat(request, path:str):
    print('AI chat')
    user_input = request.rfile.read(int(request.headers['Content-Length'])).decode('utf-8')
    if(within_rate_limit() == False):
        request.send_response(429)
        request.send_header('Connection', 'keep-alive')
        request.send_header('Content-Length', 0)
        request.send_header('Access-Control-Allow-Origin', '*')
        request.end_headers()
        # request.finish_log(429, 'chat', 0)
        request.wfile.write(b'')
        request.wfile.flush()
        return
    history:list = json.loads(user_input)
    history.insert(0, {'role': 'system', 'content': PROMPT})
    error_msg = ''
    log_queue.put(json.dumps({'history': history}, ensure_ascii=False))
    success, error_msg, result = get_gpt_resp(history)
    if(error_msg != ''):
        request.send_response(500)
        error_msg = error_msg.encode('utf-8')
        request.send_header('Content-Length', len(error_msg))
        request.send_header('Connection', 'keep-alive')
        request.send_header('Access-Control-Allow-Origin', '*')
        request.end_headers()
        # request.finish_log(500, 'chat', len(error_msg))
        request.wfile.write(error_msg)
        request.wfile.flush()
        return
    # here the response must be legal
    history.pop(0)
    # history.append({'role': 'assistant', 'content': response.choices[0].message.content})
    messages = []
    formatted = format_gpt_resp(result)
    # formatted = json.dumps(json.loads(result, strict=False), ensure_ascii=False, indent=2)
    # formatted = 'This is the raw response from GPT, have not called functions.\n\n' + formatted
    # messages.append({'type': 'text', 'content': formatted})
    messages = generate_messgae(formatted)
        
    request.send_response(200)
    resp_data = json.dumps({'history': history, 'messages': messages}, ensure_ascii=False)
    resp_data = resp_data.encode('utf-8')
    request.send_header('Content-Length', len(resp_data))
    request.send_header('Connection', 'keep-alive')
    request.send_header('Access-Control-Allow-Origin', '*')
    request.end_headers()
    # request.finish_log(200, 'chat', len(resp_data))
    request.wfile.write(resp_data)
    request.wfile.flush()
    return

log_file = None
log_queue = Queue()

try:
    f = open(LOG_PATH, 'r')
except:
    log_file = open(LOG_PATH, 'w')
if (log_file == None):
    f.close()
    log_file = open(LOG_PATH, 'a')
    log_file.write('\n\n')


def write_logs():
    log_file.write(format(time() * 1000, '.3f') + ': Server started\n')
    log_file.flush()
    while True:
        l = log_queue.get()
        current_time = format(time() * 1000, '.3f')
        l = current_time + ': ' + l + '\n'
        log_file.write(l)
        log_file.flush()

start_new_thread(write_logs, ())
