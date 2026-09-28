// Demonstrations shown in the Data Example viewer and the EmbRACE Viewer, taken from
// the training environments. Each step carries its egocentric frame, action and rationale.
const EMBRACE_DATA = {
  "Basic": {
    "x014310_y005957_z-012705_t0_b": {
      "map": "Map_ChemicalPlant_1",
      "instruction": "Head toward the wooden cable spool.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg"
      ],
      "actions": [
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "The wooden cable spool with its coiled cable sits ahead against the concrete building wall, but it lies to the right of my current heading. I will turn right to bring it closer to straight ahead so the open concrete yard becomes a clear walking line toward it.",
        "The spool now stands roughly ahead of me across flat concrete, with the tall equipment housing well to my right and no obstruction in my path. I will step forward along this heading to begin closing the distance.",
        "The spool has grown noticeably larger and stays near the middle of my view, so my heading is still good. I continue walking forward over the open slab to keep closing the gap.",
        "The spool is clearly closer, its wooden flange and wound cable now easy to make out against the metal wall behind it. Nothing blocks the remaining stretch, so I take another step forward.",
        "The spool now dominates the middle of my view and I can see its base resting on the concrete a short distance away. I will move forward again to finish closing in on it.",
        "The spool fills much of my view and its top rim is above my eye line, so only a short gap remains. One more step forward should bring me right up beside it.",
        "The wooden cable spool's coils and wooden rim are directly in front of me at arm's length. The task is complete, so further movement is unnecessary."
      ]
    },
    "x001593_y-002796_z000143_t0_a": {
      "map": "VictorianTrainStation",
      "instruction": "Walk to the bench located next to the phone booth.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "I can see the red phone booth ahead against the station wall, with a wooden bench immediately to its right, so that bench is my target. My heading already points down the walkway toward it, so I will step forward to begin closing the gap.",
        "The phone booth and the bench beside it now appear larger and lower in my view, confirming I am walking straight at them. The tiled floor ahead stays clear, so I will continue forward without adjusting my heading.",
        "The booth now fills the left side of my view and the bench next to it sits just ahead with the litter bin at its far end. I am still a couple of steps short of standing at that bench, so I will keep moving forward.",
        "I have drawn level with the edge of the phone booth, and the bench beside it lies just ahead and slightly left along the wall. Another forward step should bring me right up alongside its seat.",
        "The bench now occupies most of the near ground in front of me, with the litter bin at its right end within arm's reach. One more short step should place me directly at the bench beside the phone booth.",
        "I am standing right at the wooden bench beside the phone booth, its seat within arm's reach. The task is complete, so I stop here."
      ]
    },
    "x-000231_y-001772_z000398_t0_b": {
      "map": "Storagehouse",
      "instruction": "Head toward the yellow \"A Sector\" marking on the wall.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "I can see the yellow \"A SECTOR\" lettering painted on the red wall to my right, further down the corridor. The floor ahead is clear, so I will move forward along the corridor to close distance toward that marking.",
        "The painted letter on the right wall now fills much more of my view, confirming I am drawing nearer to it. The passage ahead remains unobstructed, so another step forward should bring me alongside the marking.",
        "I am now nearly level with the marked wall, but the lettering has slid to the far right edge of my view while I face straight down the corridor. Turning right should swing my heading toward the painted wall panel.",
        "The large yellow \"A\" is now clearly in view on my right, though still off to the side rather than centered ahead of me. I will turn right again to bring the marking squarely in front of my heading.",
        "I am now facing the red wall panel with the yellow \"A SECTOR\" lettering directly in front of me, but there is still a gap of open floor between us. Moving forward should place me right at the marking.",
        "The yellow \"A\" marking fills my view directly ahead at close range. The task is complete, so further movement is unnecessary."
      ]
    }
  },
  "Exploration": {
    "x-000097_y-000060_z000098_t1_a": {
      "map": "Storagehouse",
      "instruction": "Explore the area to find the red door beneath the D Sector sign, then walk toward it.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg"
      ],
      "actions": [
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "From here I only see storage racks, a yellow covered pallet and an A1 bay marker, so neither the D Sector sign nor a red door is in view. I will turn left to begin a steady scan of the surrounding bays for that signage.",
        "Rotating has opened up an aisle to the left where large wall lettering ending in TOR is partially visible above a workbench area, which looks like a sector sign. I will keep turning left in the same direction to bring that lettering and the wall beneath it fully into view.",
        "The D SECTOR sign is now readable on the far wall and a red door sits directly beneath it, but both are off to my left with racking crowding the right side of my view. I will turn left once more to place that red door near the center of my heading before walking.",
        "The red door under the D SECTOR sign is now centered ahead of me with clear blue floor between us. I will walk forward along this open lane to close the distance to the door.",
        "The red door has grown larger and stays aligned with my heading, and the floor in front of me is still clear of pallets and boxes. I will keep walking forward to continue closing on it.",
        "I am now close enough to see the door's handle, threshold and the EXIT light above it, with the boxes and shelving remaining to my right rather than in my path. Another step forward should bring me right up to the door.",
        "The red door and its frame now dominate my view just a short step away, with the first aid board and table clear of my line of travel. I will take one more step forward to stand directly at the door.",
        "The red door fills my view at arm's length, its handle directly in front of me. The task is complete, so I stop here."
      ]
    },
    "x003491_y-057028_z002608_t1_a": {
      "map": "Demo_Roof",
      "instruction": "Search for a stack of wooden pallets sitting near a brick wall, then navigate over to them.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg"
      ],
      "actions": [
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "From this rooftop terrace I only see the railing, open sky, and neighboring facades, with no stack of pallets anywhere in front of me. The brick wall of my own building rises on my left, which is the most plausible place for pallets to be stored against, so I will turn left to scan along it.",
        "The brick wall now fills the left half of my view, but the rooftop deck beside it is empty of any stacked material. I will continue turning left in the same direction to bring more of the wall base and the unseen corner of the terrace into view.",
        "A stack of wooden pallets is now visible at the base of the brick wall on the left side of my view, next to a covered tarp and the painted lettering. I will turn left once more to bring that stack closer to the center of my heading before advancing.",
        "The pallet stack sits ahead of me against the brick wall, roughly aligned with my heading. The deck between us is clear, so I will walk forward to close the distance toward the pallets.",
        "The pallets now appear noticeably larger and more centered, confirming I am closing on them along the brick wall. The path is still clear, so I will keep walking forward to get right up to the stack.",
        "The stack of pallets now dominates my view and the brick wall behind it is only a short distance away. I will take one more step forward to stand directly at the pallets.",
        "The stacked wooden pallets and the brick wall fill my view at arm's length. The task is complete, so I stop here."
      ]
    },
    "x-005924_y002285_z000139_t1_a": {
      "map": "Tokyo",
      "instruction": "Explore the nearby sidewalks for the parked green bicycle, then go to it.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg"
      ],
      "actions": [
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "I am facing a shopfront wall and shuttered windows, with only a narrow strip of sidewalk visible at the bottom of my view and no bicycle anywhere in it. Turning left should swing my view along the sidewalk line where parked bikes would plausibly stand.",
        "The sidewalk now opens up ahead with benches and yellow guard rails, but I still see no parked bicycle in this stretch. I will keep rotating left in the same direction to bring more of the walkway and the street edge into view.",
        "A green bicycle is now parked at the far end of the sidewalk on the left side of my view, beyond the benches and railings. I will continue turning left to bring it closer to the center of my heading before walking toward it.",
        "The green bicycle is now visible ahead along the sidewalk, standing near the curb past the bench and yellow railings. The path in front of me looks clear, so I will walk forward to close the distance toward it.",
        "The green bicycle has grown larger and remains slightly left of my heading beside the bench and rails. I will keep stepping forward along this clear stretch to reduce the remaining distance.",
        "The bicycle is now clearly framed just ahead on the left, parked against the curb near the pillar. Another step forward should bring me close enough to be at it.",
        "The green bicycle now fills much of the left side of my view, only a short distance away beside the pillar. I will take one more step forward to stand directly at it.",
        "The green bicycle stands immediately beside me, filling the near left of my view. The task is complete, so I stop here."
      ]
    }
  },
  "Dynamic_Spatial-Semantic": {
    "x-003270_y-000115_z000098_t2_c": {
      "map": "SuburbNeighborhood_Day",
      "instruction": "Go to the third concrete roadblock from the left.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "Four concrete barriers span the street ahead, and counting from the left edge my target is the third, the one standing just left of the centerline next to a yellow ROAD CLOSED trestle. It is still far down the block, so I will walk forward to close that distance.",
        "The barrier I picked, the one by the centerline with the trestle at its side, now reads noticeably larger but is still a good stretch away. Nothing blocks the open lane in front of me, so I will keep walking straight toward it.",
        "The barriers at the far left of the row are sliding out of my view, so I hold onto the one I chose, the barrier next to the centerline with the trestle beside it, rather than recounting from an end I can no longer see. It sits ahead and slightly right, and I will keep advancing.",
        "At this range my target barrier no longer lies on my heading; it sits off to the right of straight ahead while a trestle and another barrier crowd my left. A modest turn to the right should put it squarely in front of me before I take the last step.",
        "The concrete barrier I chose is now centered low in my view with clear pavement between us. One more step forward should bring me right up to it.",
        "The concrete barrier I chose stands directly in front of me, filling my lower view. I have reached it, so I stop here."
      ]
    },
    "x003143_y014629_z-012713_t2_d": {
      "map": "Map_ChemicalPlant_1",
      "instruction": "Navigate to the second cone from the left.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "Two orange cones stand on the deck ahead among slim striped posts; the second from the left is the one right of centre, roughly in line with the blue barrels. It lies to the right of my heading, so I turn right to face it.",
        "The cone I picked, the one standing in line with the stack of blue barrels, now sits near the middle of my view. The concrete between us is open and clear, so I walk forward to close the distance.",
        "The cone by the barrels has grown larger and stays centred in front of me, confirming my heading is good. A long stretch of deck still separates us, so I keep walking forward.",
        "The cone stands squarely ahead with its stripes clearly readable, yet it is still a few paces away from me. I advance again along the same line.",
        "The cone now fills much of the lower view but I am not yet beside it. The other cone has dropped out of my view to the left, so I simply keep following this one and step forward to cover the last stretch.",
        "The cone stands directly at my feet, filling the near view. I have reached it, so there is no reason to move further."
      ]
    },
    "x001218_y-000579_z000099_t2_b": {
      "map": "Supermarket",
      "instruction": "Go to the second green chair from the right along the wall.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "Counting the green chairs along the window wall from the right end, the pair nearest the trash bin gives me my target: the second one in, which stands right beside the tall Drylands DairyGoods banner. Since the chairs are identical, I will hold onto that banner as my marker and walk straight ahead to close the distance.",
        "The chair beside the banner sign is still well ahead across the open tiled floor, with nothing between me and it. I will keep walking straight to bring it closer.",
        "My chair beside the banner has grown noticeably larger and sits slightly right of my heading, so my current direction remains good. I will continue forward to shorten the remaining gap.",
        "Only two green chairs remain in view now that the far left ones have slid out of sight, and mine is the one hugging the banner. I will step forward again to reach it.",
        "The chair pressed against the banner now fills much of my view just ahead and to the right. One more step forward should place me right at it.",
        "The green chair beside the banner fills my view directly ahead within reach. The task is complete, so I stop here."
      ]
    }
  },
  "Multi-stage": {
    "x003409_y019176_z027048_t3_a": {
      "map": "Old_Town",
      "instruction": "Walk to the door near the ivy, then head toward the door without ivy.",
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
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MidwayTarget",
        "TurnLeft",
        "TurnLeft",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "From under the archway I can see the small courtyard ahead, with a plain door on the left wall and another door on the right where ivy trails down the stonework. I will walk forward to clear the arch and get into the open court where both doors are reachable.",
        "Now inside the courtyard, the door draped with ivy stands on my right, while the bare door sits on the opposite wall. I will turn right to bring the ivy-covered door in front of me before walking to it.",
        "The arched door with ivy spilling over its frame is now ahead of me on the right side of the court, still several paces away. I will walk forward to close that distance.",
        "The ivy-hung door is much larger in view now, with its handle clearly visible and the potted plant beside its threshold. I am not yet beside it, so I will step forward again to stand at the door.",
        "The ivy tumbles right down the frame beside me and the door's handle is within arm's reach. I have arrived at the ivy-covered door, and I mark reaching it before setting off across the court to the bare door on the far wall.",
        "Standing at the ivy-clad door, my view is filled by its planks and the leaves beside it, so the bare door is somewhere behind my left shoulder. I will turn left to swing my heading away from this wall and back toward the open court.",
        "The courtyard has opened up ahead, but only the corner wall and its potted plants are centred, with the door I want still further round to the left. I will turn left again to keep bringing that plain door into view.",
        "The bare arched door has come into sight at the left edge of my view, set in the plain stone wall with no ivy on it. I will turn left once more to put it squarely in front of me before walking over.",
        "The plain arched door sits squarely ahead now, its stone surround clear of any climbing greenery. My heading lines up with it, so I will walk straight forward to close the gap.",
        "The ivy-free door now fills most of my view and its handle is visible, but I am still a stride short of standing right at it. One more step forward should bring me up to the doorway.",
        "I am standing right at the plain door's handle, with only bare stone beside it and no ivy. The task is complete, so there is nothing further to do."
      ]
    },
    "x000004_y-000523_z000100_t3_b": {
      "map": "Hotel_Corridor",
      "instruction": "Head toward the gold-framed painting, then proceed to the red suitcase.",
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
        "MidwayTarget",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "The gold-framed painting hangs on the left wall of this corridor, well off to the side of my current heading. I will turn left so that wall and its painting come into the center of my view before I start walking. That should give me a clean line toward it.",
        "The gold-framed painting is now ahead on the left wall and the carpeted corridor in front of me is clear. I will walk forward to close the distance toward it.",
        "The gold-framed painting has grown noticeably larger on the left wall, so my heading is carrying me toward it. Only the standing ashtray bin sits near that stretch of wall, and it does not block my line. Another step forward should bring me alongside the painting.",
        "The gold-framed painting now fills the left edge of my view at arm's reach, its frame and glass close enough to see the texture. I have arrived at the painting. I mark reaching it, and now I turn my attention to the red suitcase further along the corridor.",
        "Standing this close to the painting, the wall blocks most of my view and I cannot yet see the red suitcase. I will turn right to swing my heading back into the open corridor where the luggage stands. That should start bringing the suitcase into view.",
        "The corridor has opened up and I can now make out the red suitcase beside the brass luggage cart, but it still sits right of my center. Another turn right should line my heading up with it before I walk.",
        "The red suitcase now sits ahead beside the brass bellhop cart, roughly centered in my path. The carpet between us is open, so I will walk forward to close on it.",
        "The red suitcase and the cart beside it have grown larger ahead of me, confirming my heading is good. I am still several paces short of it, so I will keep walking forward.",
        "The red suitcase stands upright on the tiled strip beside the brass luggage cart, still several paces ahead on my right. My heading down this corridor lines up with it cleanly, with open carpet between us. I will keep walking forward to close that remaining gap.",
        "The red suitcase is now large in the lower right of my view, close to the guest room door, but I am still slightly short of standing beside it. One more step forward should bring me right up alongside it.",
        "The red suitcase is directly beside me at arm's reach on the right. The task is complete, so I stop here."
      ]
    },
    "x000054_y-006331_z000098_t3_e": {
      "map": "Storagehouse",
      "instruction": "Move to the FRAGILE labeled box on rack 07, then approach the blue barrel.",
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
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "MidwayTarget",
        "TurnRight",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Finish"
      ],
      "thinking": [
        "The rack under the 07 sign stands to my left, with cartons stencilled FRAGILE on its lower bays, while the open aisle ahead leads away from it. I will turn left to put that rack and its fragile-marked cartons squarely in front of me before walking in.",
        "The rack carrying the 07 sign is now ahead on my left, and the carton stencilled FRAGILE sits at its base beside the yellow post guard. The floor between me and it is clear, so I will walk forward to close that gap.",
        "The FRAGILE carton on the low shelf of the 07 rack is much larger in view now, but I am still a couple of paces short of standing beside it. The lane past the yellow guard remains unobstructed, so I will step forward again.",
        "The FRAGILE stencilled carton on rack 07 is right beside me, close enough to read its lettering at arm's length. I have reached the fragile-labelled box, so I mark arriving here before setting off toward the blue barrel further down the hall.",
        "Standing at the fragile-labelled carton, my view is filled by the rack face, so I need to swing toward the open hall where the barrels stand on their trolley. I will turn right to bring that far wall and the barrels into my heading.",
        "The pair of blue barrels on the wheeled trolley has come into view against the brick wall, but they still sit off to my right rather than straight ahead. I will turn right once more to line my walking direction up with them.",
        "The blue barrels on their trolley now sit near the middle of my view against the brick wall, with racks framing a clear lane on both sides. I will walk forward down that lane to close the distance to them.",
        "The blue barrels are noticeably nearer and centred ahead behind their red trolley rail, yet still several paces off. Nothing blocks the painted floor between us, so I will keep walking toward them.",
        "The two blue barrels sit on their low trolley against the brick wall, a little left of my heading but well within the open bay ahead. Only cables cross the painted floor between us, so I will keep advancing to shorten the remaining gap.",
        "The barrels and the red rail around their trolley are now clearly resolved just left of centre, with the wall behind them filling the end of the bay. I am still several paces off, so another step forward should bring me close to them.",
        "I can now make out the lids and the mottled sheen on the barrels, and the red guard rail stands only a short walk ahead. A further step should put me right at the trolley rather than looking at it from across the bay.",
        "The pair of barrels fills most of my view behind the red rail, but there is still a little floor between me and that rail. I will take one more short step to stand directly at them.",
        "The blue barrels are directly in front of me, their lids and the trolley rail within arm's reach. The task is complete, so there is nothing further to approach."
      ]
    }
  },
  "Interaction_Open-Door": {
    "x-000031_y-001060_z000132_t4_a": {
      "map": "SuburbNeighborhood_Day",
      "instruction": "Cross the garden path to the dark grid-window door on the blue house and open it.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg",
        "007.jpg",
        "008.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "TurnLeft",
        "MoveForward",
        "MoveForward",
        "OpenDoor",
        "Finish"
      ],
      "thinking": [
        "The blue house's dark door with the small grid window sits on the covered porch to my left, and a paved garden path runs forward past the flower beds. I will move forward along that path to close the large gap before turning toward the porch.",
        "The grid-window door has grown larger on my left and the porch decking in front of it is now clearly visible, but I am still out on the walkway. I will continue forward along the clear paving to reach a point beside the porch steps.",
        "I have drawn level with the porch, and the target door is now off at the left edge of my view while I am facing along the house wall. Turning left should bring the dark grid-window door into the center of my view so I can walk straight at it.",
        "The dark grid-window door is now framed on the left of my view with the wooden porch deck open in front of me. I will move forward onto the deck to shorten the distance to the door.",
        "I am on the porch, but the door has slid to the far left of my view and I am aimed at blank siding and the railing. A left turn should square me up with the door face before I step in for the handle.",
        "The dark door with its nine-pane grid window is now centered ahead of me with clear decking in between. I will step forward to bring the brass knob within reach.",
        "The door now fills most of my view and the brass knob is plainly visible on its right side, but I am still a step short of contact range. I will advance once more to stand directly at the threshold.",
        "I am pressed right up against the dark door, with its brass knob and the pane frame filling my view at arm's length. This is the target door on the blue house, so I will try the knob to open it.",
        "I see the door standing open with the interior room visible ahead of me. My task is complete, so I stop here."
      ]
    },
    "x-002040_y002287_z000169_t4_a": {
      "map": "SuburbNeighborhood_Day",
      "instruction": "Open the white paneled door between the two framed pictures.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "OpenDoor",
        "Finish"
      ],
      "thinking": [
        "The white paneled door sits ahead of me at the end of this short hallway, with a framed picture on the left wall and another on the right above the cabinet, matching the target described in the task. It is still far out of arm's reach, so I will move forward along the open floor toward it.",
        "The paneled door now fills much more of my view and its brass knob and lever are clearly visible, so I am closing on the right target. I am still a step or two short of interaction range, so I will advance again.",
        "I am close to the door face and the lever handle is visible at the right of my view, but the panels and jamb still read slightly off to my side rather than squarely in front. A short further step should bring the handle within comfortable reach before I try it.",
        "At this distance the door's handle and keyhole sit toward the right edge of my view while the jamb and wall occupy the left, so I am not squarely facing the panel. Turning right should center the lever in front of me for a clean interaction.",
        "The lever handle and keyhole are now centered directly in front of me at close range, so the door is squarely within reach. I will operate the handle to try to open this white paneled door.",
        "I see the door swung open with the space and shelving beyond it revealed. My task is complete, so I stop here."
      ]
    },
    "x000207_y001964_z000168_t4_a": {
      "map": "suburbNeighborhood_Night",
      "instruction": "Open the white paneled door on the same wall as the curved black pipe.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "TurnRight",
        "MoveForward",
        "OpenDoor",
        "MoveForward",
        "OpenDoor",
        "Finish"
      ],
      "thinking": [
        "The curved black pipe runs down the concrete wall ahead of me, and the white paneled door on that same wall is cut off at the right edge of my view. I will turn right so the door and its handle sit centered in front of me before I move toward it.",
        "The white paneled door is now framed squarely ahead with its brass lever handle plainly visible, and the pipe on the same wall confirms this is the target. I am still several steps back, so I will move forward to close the gap and bring the handle within reach.",
        "The brass lever and deadbolt now fill my view, so I am standing right at the door face on the correct wall. I will try to operate the handle and open this white paneled door.",
        "My attempt at the handle did not move the door, since it still sits closed and flush in its frame exactly as before. I may not be close enough for the interaction to register, so I will step forward a little to tighten my position against the handle.",
        "After the earlier attempt left the door shut, I have closed in further and the lever and deadbolt are now large and directly in front of me. I will try the handle again from this tighter position, which should let the latch release and swing the door open.",
        "I see the white paneled door standing open, with the room and staircase beyond it in clear view. My task is complete, so I stop here."
      ]
    }
  },
  "Interaction_Pick-and-Drop": {
    "x003019_y-007965_z000138_t5_a_pd": {
      "map": "eastern_Garden",
      "instruction": "Pick up the candelabra, then place it next to the stone lantern.",
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
        "009.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "Pick",
        "TurnRight",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "Drop",
        "Finish"
      ],
      "thinking": [
        "The candelabra stands on the mossy ground ahead of me, near the base of the blossoming tree, and the stone lantern sits off to the right against the rock face. It is still too far for me to grasp, so I will walk straight forward to close the gap.",
        "The candelabra is noticeably larger and lower in my view now, but it remains beyond comfortable reach. I will step forward again so it comes close enough in front of me for a grasp attempt.",
        "The candelabra now fills the lower part of my view directly in front of me, its three candles and silver arms clearly within reach. This is the right distance to attempt the grasp, so I will try to pick it up.",
        "The candelabra is now in my hands rather than resting on the ground, so the grasp took hold. The stone lantern lay off to my right when I approached, so I will turn right to bring it into view and face the delivery spot.",
        "The stone lantern is now visible ahead of me at the foot of the stone stairway, with the carried candelabra still in hand. It is still several paces away, so I will walk forward to carry the candelabra closer to it.",
        "The lantern sits right of my current heading, closer now but offset toward the stairs rather than straight ahead. I will turn right to center it so my remaining steps lead directly to it.",
        "The lantern is now roughly centered in front of me with the candelabra still carried. A short walk forward should bring me near enough to set the candelabra beside it.",
        "The lantern is close and centered, its lit red panel clearly visible, but I am not yet beside it. I will take one more step forward so the candelabra can be released right next to the lantern.",
        "The candelabra is still in my hands and the stone lantern now stands directly ahead, filling the near view at arm's length. This is the placement spot the task asks for, so I will release the candelabra here beside the lantern. It should settle on the ground right next to its base.",
        "The candelabra now rests on the ground beside the stone lantern instead of in my hands. The task is complete, so I stop here."
      ]
    },
    "x014310_y005957_z-012705_t5_b_p": {
      "map": "Map_ChemicalPlant_1",
      "instruction": "Lift the jerry can at the wooden cable spool.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg",
        "006.jpg"
      ],
      "actions": [
        "MoveForward",
        "MoveForward",
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "Pick",
        "Finish"
      ],
      "thinking": [
        "I can see the wooden cable spool ahead on the right side of the yard, with a small red jerry can standing on the concrete just to its left. The can is still far off across the open apron, so I will walk forward to close that distance. This straight advance should keep both the spool and the can in view as they grow larger.",
        "The jerry can beside the cable spool is noticeably larger now, but it is still several strides away and too distant to reach. Nothing blocks the flat concrete between us, so I will keep walking forward. Another step should bring the can close enough to fine tune my heading.",
        "The jerry can and the wooden spool now sit clearly right of my heading, while my current facing points along the building wall toward the tanks. Continuing straight would carry me past them rather than to them. I will turn right to bring the can into the center of my view before advancing again.",
        "After turning, the jerry can and the cable spool sit squarely in the middle of my view with the traffic cone beside them. The heading looks correct, but the can is still a couple of strides off. I will step forward to close in on it.",
        "The jerry can is now low and large in the lower left of my view, close but not yet within comfortable reach. One more forward step should place me directly beside it at the foot of the wooden spool. I will advance again before attempting the lift.",
        "The jerry can is right at my feet in the near left foreground, with the wooden spool beside me, so I am standing at the intended pickup spot. This is the closest I can get without stepping over it. I will reach down and try to lift the can now.",
        "The red jerry can is now held in my hands in front of me. The task is complete, so I stop here."
      ]
    },
    "x-010752_y-005997_z001218_t5_a_p": {
      "map": "AsianMedivalCity",
      "instruction": "Pick up the plate near the red wooden lamp post.",
      "images": [
        "000.jpg",
        "001.jpg",
        "002.jpg",
        "003.jpg",
        "004.jpg",
        "005.jpg"
      ],
      "actions": [
        "TurnRight",
        "MoveForward",
        "MoveForward",
        "MoveForward",
        "Pick",
        "Finish"
      ],
      "thinking": [
        "The white plate and the red wooden lamp post behind it sit off to my right side of the courtyard, so my current heading would carry me past them toward the long veranda ahead. I will turn right to bring the plate and its lamp post closer to the center of my view before walking. That should give me a straight approach line across the paving.",
        "The plate now sits near the middle of my view with the red lamp post standing just beyond it, confirming my heading is right. The plate is still far off across the stone courtyard, well out of reach. I will walk forward over the clear paving to close that distance.",
        "The plate has grown noticeably larger and stays centered under the red lamp post, so my line of travel remains correct. It is still several paces away and too distant to grasp. I will keep walking straight toward it.",
        "The plate now fills a good part of the lower view and the red lamp post rises right behind it, so I am nearly there. A final step should place the plate within arm's reach rather than stopping short. I will advance once more before attempting the grasp.",
        "The plate is now directly in front of me at close range, with the red wooden lamp post standing immediately beyond it. Nothing separates me from it, so this is the moment to reach out. I will attempt to pick up the plate.",
        "The plate is now held in my hands. The task is complete, so I stop here."
      ]
    }
  }
};

// Display names for the task-type dropdown, matching the paper.
const TYPE_LABELS = {
  "Basic": "Basic",
  "Exploration": "Exploration",
  "Dynamic_Spatial-Semantic": "Dynamic Spatial-Semantic",
  "Multi-stage": "Multi-stage",
  "Interaction_Open-Door": "Open Door",
  "Interaction_Pick-and-Drop": "Pick & Drop"
};

const ACTION_COLORS = {
    "MoveForward": "#388E3C",
    "MoveBackward": "#388E3C",
    "JumpForward": "#388E3C",
    "TurnLeft": "#7C4DFF",
    "TurnRight": "#7C4DFF",
    "LookUp": "#EA80FC",
    "LookDown": "#EA80FC",
    "LookBack": "#EA80FC",
    "LookHand": "#EA80FC",
    "OpenDoor": "#E64A19",
    "PickObject": "#E64A19",
    "DropObject": "#E64A19",
    "Finish": "#FBC02D",
    "MidwayTarget": "#29B6F6"
};

let currentStep = 0;
let imageList = [];
let thinkingList = [];
let actionList = [];
let basePath = "";
let currentType = "";
let currentTask = "";

// ----------------------------------------------------
// Update the display
// ----------------------------------------------------
function updateDisplay() {
    const img = document.getElementById("step-image");
    img.src = `${basePath}/${imageList[currentStep]}`;

    document.getElementById("step-id").innerHTML =
        `<span class="ex-step-now">${currentStep + 1}</span>` +
        `<span class="ex-step-sep">/</span>` +
        `<span class="ex-step-all">${imageList.length}</span>` +
        `<span class="ex-step-word">steps</span>`;

    const action = actionList[currentStep];
    const color = ACTION_COLORS[action] || "#999";
    document.getElementById("action-box").innerHTML =
        `<span class="ex-pill" style="background:${color};">${action}</span>`;

    document.getElementById("thinking-box").textContent = thinkingList[currentStep];
    document.getElementById("thinking-box").scrollTop = 0;

    document.getElementById("prev-step").disabled = currentStep === 0;
    document.getElementById("next-step").disabled = currentStep === imageList.length - 1;

    const dots = document.getElementById("step-dots").children;
    for (let i = 0; i < dots.length; i++) {
        dots[i].classList.toggle("is-on", i === currentStep);
    }
}

// One dot per step, so the reader can see how long the demonstration is and jump within it.
function buildDots() {
    const box = document.getElementById("step-dots");
    box.innerHTML = "";
    for (let i = 0; i < imageList.length; i++) {
        const d = document.createElement("button");
        d.className = "ex-dot";
        d.type = "button";
        d.title = `Step ${i + 1}`;
        d.addEventListener("click", () => { currentStep = i; updateDisplay(); });
        box.appendChild(d);
    }
}


// ----------------------------------------------------
// Load data (from EMBRACE_DATA)
// ----------------------------------------------------
function loadData(taskType, taskItem) {

    currentType = taskType;
    currentTask = taskItem;

    const data = EMBRACE_DATA[taskType][taskItem];

    basePath = `static/data/${taskType}/${taskItem}`;

    imageList = data.images;
    thinkingList = data.thinking;
    actionList = data.actions;

    document.getElementById("instruction").innerHTML =
        `<span class="lab">Instruction:</span><span class="txt">${data.instruction}</span>`;

    currentStep = 0;
    buildDots();
    updateDisplay();
}

// ----------------------------------------------------
// Task type change
// ----------------------------------------------------
document.getElementById("task-type").addEventListener("change", () => {
    const type = document.getElementById("task-type").value;
    const taskSelect = document.getElementById("task-item");

    taskSelect.innerHTML = "";

    Object.keys(EMBRACE_DATA[type]).forEach(taskKey => {
        const opt = document.createElement("option");
        opt.value = taskKey;
        // Each example of a type comes from a different environment, so the
        // environment name identifies it better than the pose-derived key.
        const entry = EMBRACE_DATA[type][taskKey];
        opt.textContent = entry.map ? entry.map.replace(/_/g, " ") : taskKey;
        taskSelect.appendChild(opt);
    });

    taskSelect.dispatchEvent(new Event("change"));
});

// ----------------------------------------------------
// Task item change
// ----------------------------------------------------
document.getElementById("task-item").addEventListener("change", () => {
    const type = document.getElementById("task-type").value;
    const task = document.getElementById("task-item").value;

    loadData(type, task);
});

// ----------------------------------------------------
// Step buttons
// ----------------------------------------------------
document.getElementById("prev-step").addEventListener("click", () => {
    if (currentStep > 0) {
        currentStep--;
        updateDisplay();
    }
});

document.getElementById("next-step").addEventListener("click", () => {
    if (currentStep < imageList.length - 1) {
        currentStep++;
        updateDisplay();
    }
});

// ----------------------------------------------------
// Initialize dropdown (based on EMBRACE_DATA)
// ----------------------------------------------------
function initViewer() {
    const typeSelect = document.getElementById("task-type");
    typeSelect.innerHTML = "";

    Object.keys(EMBRACE_DATA).forEach(type => {
        const opt = document.createElement("option");
        opt.value = type;
        opt.textContent = TYPE_LABELS[type] || type;
        typeSelect.appendChild(opt);
    });

    typeSelect.dispatchEvent(new Event("change"));
}

initViewer();
console.log("Viewer initialized with EMBRACE_DATA.");

// Left and right arrow keys walk the demonstration, unless a dropdown has focus.
document.addEventListener("keydown", (e) => {
    const tag = (document.activeElement && document.activeElement.tagName) || "";
    if (tag === "SELECT" || tag === "INPUT" || tag === "TEXTAREA") return;
    if (e.key === "ArrowLeft" && currentStep > 0) { currentStep--; updateDisplay(); }
    if (e.key === "ArrowRight" && currentStep < imageList.length - 1) { currentStep++; updateDisplay(); }
});
