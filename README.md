# SOMNUS PROJECT


"""
{
  "operacao": "SUM_BY_SUBSCALE",
  "subescalas": {
    "dass_depressao": ["dassc", "dasse", "dassj", "dassm", "dassp", "dassq", "dassu"],
    "dass_ansiedade": ["dassb", "dassd", "dassg", "dassi", "dasso", "dasss", "dasst"],
    "dass_estresse": ["dassa", "dassf", "dassh", "dassk", "dassl", "dassn", "dassr"]
  }
},

{
  "operacao": "SUM",
  "variaveis": [
    "k10a", "k10b", "k10c", "k10d", "k10e", 
    "k10f", "k10g", "k10h", "k10i", "k10j"
  ],
  "limiares": [
    { "max": 19, "status": "Baixo risco" },
    { "max": 50, "status": "Provável transtorno" }
  ]
},

{
  "operacao": "SUM",
  "variaveis": [
    "rsqa", "rsqb", "rsqc", "rsqd", "rsqe", "rsqf", "rsqg", "rsqh", "rsqi", "rsqj",
    "rsqk", "rsql", "rsqm", "rsqn", "rsqo", "rsqp", "rsqq", "rsqr", "rsqs", "rsqt"
  ],
  "limiares": [
    { "max": 6, "status": "Sem indícios de TMC" },
    { "max": 20, "status": "Suspeita de TMC" }
  ]
},

{
  "operacao": "SUM",
  "variaveis": [
    "sonolea", "sonoleb", "sonolec", "sonoled", 
    "sonolee", "sonolef", "sonoleg", "sonoleh"
  ],
  "limiares": [
    { "max": 10, "status": "Normal" },
    { "max": 24, "status": "Sonolência Diurna Excessiva" }
  ]
},

{
  "operacao": "SUM",
  "variaveis": [
    "audit1", "audit2", "audit3", "audit4", "audit5", 
    "audit6", "audit7", "audit8", "audit9", "audit10"
  ],
  "limiares": [
    { "max": 7, "status": "Baixo Risco" },
    { "max": 15, "status": "Uso de Risco" },
    { "max": 19, "status": "Uso Nocivo" },
    { "max": 40, "status": "Provável Dependência" }
  ]
},

{
  "operacao": "SUM_BY_SUBSCALE",
  "subescalas": {
    "suporte_familia": ["emsspec", "emssped", "emsspeh", "emsspel"],
    "suporte_amigos": ["emsspef", "emsspeg", "emsspei", "emsspm"],
    "suporte_outros": ["emsspea", "emsspeb", "emsspee", "emsspej"]
  }
}

"""

