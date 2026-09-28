// Benchmark tasks for the EmbRACE Viewer, three per task type, from the seven
// held-out test environments. Each carries its instruction, the reference
// human demonstration (frames and actions) as recorded, and its canonical
// success-region images; test maps have no rationales.
const EMBRACE_BENCHMARK = {
  "Basic": {
    "x-005469_y-001114_z000101_t0_a": {
      "map": "Downtownwest",
      "instruction": "Walk to the small cart with an umbrella on the walkway.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x-000037_y-000027_z000230_t0_a": {
      "map": "Medieval_Daytime",
      "instruction": "Walk to the wooden door of the ivy-covered house.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x-001712_y003120_z000104_t0_b": {
      "map": "TemplePlaza",
      "instruction": "Approach the wooden barrels.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    }
  },
  "Exploration": {
    "x-018397_y000124_z000101_t1_a": {
      "map": "Downtownwest",
      "instruction": "Search for the storefront with the \"sleeve\" sign on its facade; after locating it, head to its entrance.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg",
        "015.jpg",
        "016.jpg",
        "017.jpg",
        "018.jpg",
        "019.jpg",
        "020.jpg",
        "021.jpg",
        "022.jpg",
        "023.jpg",
        "024.jpg",
        "025.jpg",
        "026.jpg",
        "027.jpg",
        "028.jpg",
        "029.jpg"
      ],
      "actions": [
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x-002886_y-008741_z000368_t1_b": {
      "map": "Greek_Island",
      "instruction": "Once you identify the four-wheeled wooden cart loaded with stacked sandbags, navigate over to reach it.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x001274_y-001929_z000211_t1_b": {
      "map": "IndustrialArea",
      "instruction": "Identify the black valve wheel mounted on a blue pipe somewhere in this room, then proceed to its location.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    }
  },
  "Dynamic_Spatial-Semantic": {
    "x001318_y007867_z000118_t2_b": {
      "map": "CourtYard",
      "instruction": "Walk to the leftmost ground-floor window at the base.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg"
      ],
      "actions": [
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "LookDown",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x-000451_y-001247_z000236_t2_a": {
      "map": "TemplePlaza",
      "instruction": "Walk to the leftmost column on the rounded building.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x000569_y-001832_z000561_t2_d": {
      "map": "IndustrialArea",
      "instruction": "Move to the second window from right.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    }
  },
  "Multi-stage": {
    "x-012624_y008792_z003794_t3_d": {
      "map": "Greek_Island",
      "instruction": "Navigate to the wooden cart near the awning, then approach the striped column base.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg",
        "015.jpg",
        "016.jpg",
        "017.jpg",
        "018.jpg",
        "019.jpg",
        "020.jpg",
        "021.jpg",
        "022.jpg",
        "023.jpg",
        "024.jpg",
        "025.jpg",
        "026.jpg",
        "027.jpg",
        "028.jpg",
        "029.jpg",
        "030.jpg",
        "031.jpg",
        "032.jpg",
        "033.jpg",
        "034.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MidwayTarget",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "midway",
          "xy": "midway_xy_region.png",
          "ue": "midway_ue_top_down_overlay.jpg"
        },
        {
          "stage": "final",
          "xy": "final_xy_region.png",
          "ue": "final_ue_top_down_overlay.jpg"
        }
      ]
    },
    "x007059_y-000713_z000101_t3_a": {
      "map": "Downtownwest",
      "instruction": "Walk to the wooden bench, then head toward the kiosk with a canopy.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg",
        "015.jpg",
        "016.jpg",
        "017.jpg"
      ],
      "actions": [
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MidwayTarget",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "midway",
          "xy": "midway_xy_region.png",
          "ue": "midway_ue_top_down_overlay.jpg"
        },
        {
          "stage": "final",
          "xy": "final_xy_region.png",
          "ue": "final_ue_top_down_overlay.jpg"
        }
      ]
    },
    "x000077_y000001_z000225_t3_a": {
      "map": "Medieval_Daytime",
      "instruction": "Walk to the wooden barrel cluster, then head toward the burlap sack.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MidwayTarget",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "regions": [
        {
          "stage": "midway",
          "xy": "midway_xy_region.png",
          "ue": "midway_ue_top_down_overlay.jpg"
        },
        {
          "stage": "final",
          "xy": "final_xy_region.png",
          "ue": "final_ue_top_down_overlay.jpg"
        }
      ]
    }
  },
  "Interaction_Open-Door": {
    "x000495_y-000053_z000225_t4_a": {
      "map": "Medieval_Daytime",
      "instruction": "Head up the wooden steps and open the large wooden door at the top of the staircase.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "OpenDoor",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x000516_y-002738_z000736_t4_a": {
      "map": "IndustrialArea",
      "instruction": "Head toward the door at the top of the staircase with the small window and open it.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "TurnLeft",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "OpenDoor",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x004255_y-001782_z000245_t4_a": {
      "map": "medieval_Nighttime",
      "instruction": "Cross the grass to the wooden door of the isolated stone-and-timber cottage and open it.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "OpenDoor",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    }
  },
  "Interaction_Pick-and-Drop": {
    "x-000845_y000281_z000106_t5_b_pd": {
      "map": "TemplePlaza",
      "instruction": "Pick up the jerry can, then leave it near the wooden shield on the left.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg",
        "015.jpg",
        "016.jpg",
        "017.jpg",
        "018.jpg",
        "019.jpg",
        "020.jpg",
        "021.jpg",
        "022.jpg"
      ],
      "actions": [
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Pick",
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "Drop",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x001527_y008193_z000118_t5_a_pd": {
      "map": "CourtYard",
      "instruction": "Pick up the wicker basket, then set it down near the red door.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg",
        "012.jpg",
        "013.jpg",
        "014.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "Pick",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "Drop",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    },
    "x-002858_y-008709_z000370_t5_a_p": {
      "map": "Greek_Island",
      "instruction": "Pick up the green bell pepper near the wooden door.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg",
        "009.jpg",
        "010.jpg",
        "011.jpg"
      ],
      "actions": [
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "Pick",
        "Finish"
      ],
      "regions": [
        {
          "stage": "final",
          "xy": "xy_region.png",
          "ue": "ue_top_down_overlay.jpg"
        }
      ]
    }
  }
};
