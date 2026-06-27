# Module Categorization (for the state→module MAP / "brain")

This categorizes all 466 AAUnlimited modules from `module_catalog.md` to feed the hand-curated
state→module MAP used by the evolution system. At an end-of-day / world-boundary resolve, accumulated
DB state (climax/kiss/H counters, bonds, virtue, training, role flags, who-dominated-whom) is
thresholded to assign or toggle pre-installed modules on cards.

Core design principle: evolution OUTCOMES are EARNED, not assigned. A character is DRIVEN INTO a
module when accumulated DB state crosses a threshold (high cum/H → Sex Addict; virtue loss →
Corruption; dominated by another race → develops PREJUDICE/HOSTILE toward that race). The same module
can be INNATE (on the card from creation) OR DEVELOPED (DB-driven) — see the `developable` column.
The `race` column + `## RACE SUBSYSTEM` define the racial-evolution axis.

## Field scheme

**function** — primary effect domain (pick ONE):
- SEXUAL — H behavior, corruption-via-sex, addiction, fetish/preference, cum/pregnancy-adjacent arousal
- PERSONALITY — virtue, traits, temperament, mood, corruption of character
- RELATIONSHIP — love/jealousy/loyalty/attachment/cheating/social bonds
- STATUS_ROLE — role/condition-based behavior (jailer, leader, prisoner-like, delinquent) — jail-relevant
- STATS_TRAINING — strength/intelligence/stamina/skill buffs, training outcomes
- PREGNANCY — fertility/pregnancy/impregnation mechanics
- BEHAVIOR_AI — NPC decision/targeting/interruption/AI behavior gating
- APPEARANCE — visual/style/outfit state
- COMBAT_VIOLENCE — murder, fighting, yandere, knives
- META_SYSTEM — utility/debug/system, not a character state

**evo_role** — role in the evolution system (pick ONE):
- TARGET — could be ASSIGNED as a transformation OUTCOME from accumulated activity/state (most important tag)
- GATE — a status set/toggled at a world transition via a card-storage flag (role/condition)
- SOURCE — its presence influences how a char develops/reacts but isn't itself an assignable outcome
- NONE — cosmetic/system/utility, not part of evolution

**relevance** — to the jail/evolution project: HIGH / MEDIUM / LOW

**uncertain** — yes/no; flagged liberally where function/evo_role is debatable or effect is unclear.

**developable** — can a character be DRIVEN INTO this module by accumulated DB state (activity
counters, relationships, experiences, who-dominated-them), as opposed to it being only an innate
starting trait? Design principle: evolution OUTCOMES are EARNED, not assigned — a character is
driven into a module when accumulated state crosses a threshold. Values:
- `yes` — an earnable/developed outcome (dual: may ALSO be innate on the card, but DB state can
  produce it). The note carries a SHORT condition hint (what would drive it). Examples: Sex Addict
  (high cum/H), Corruption (virtue loss), Prejudice-X (dominated/wronged by race X), Hunter-X
  (trauma/abuse by race X).
- `innate` — only a starting/base trait or designation; accumulated experience does not produce it
  (fixed appearance, base preference biases, a Race designation, born-with temperament).
- `gate` — assigned by a role/milestone event at a world/status transition, NOT driven by
  accumulated activity counters. Distinct from counter-accumulated TARGETs (e.g. Sex Addict): a gate
  is conferred when a role is taken on or a milestone is reached (Jailer, Detective, Banchou, Club
  Leader, Marriage, Killer), not when a threshold of accrued activity is crossed.
- `system` — META/utility/cosmetic, n/a.

**race** — RACE-subsystem modules only (else blank). Format `<target_race>:<valence>`:
- `DESIGNATION` — this char IS race X (Race-X). Innate.
- `BIAS` — more responsive/positive toward race X (Bias-X).
- `PREJUDICE` — less responsive/negative toward race X (Prejudice-X).
- `HOSTILE` — wants to harm/kill race X (Hunter-X / Natural Enemy-X / Slayer-X).
- `OBSESSION` — fixated on / loves race X (Obsession-X).
See `## RACE SUBSYSTEM` for the full per-race vocabulary and the racial-evolution axis.

## Categorization table

| Module | function | evo_role | relevance | uncertain | developable | race | note |
|---|---|---|---|---|---|---|---|
| #MeToo | SEXUAL | TARGET | MEDIUM | no | yes |  | revokes consent mid-sex; possible trauma outcome; after H trauma |
| Abstinent | SEXUAL | SOURCE | MEDIUM | no | innate |  | no sex until marriage; virtue-gated bias |
| Accommodating | SEXUAL | TARGET | LOW | no | yes |  | submissive H role; repeated submissive H |
| Adaptive | SEXUAL | SOURCE | MEDIUM | no | innate |  | copies H prefs from lovers; dev modifier |
| Admires Dum | PERSONALITY | SOURCE | LOW | no | innate |  | partner-preference bias |
| Admires Fit | PERSONALITY | SOURCE | LOW | no | innate |  | partner-preference bias |
| Admires Wit | PERSONALITY | SOURCE | LOW | no | innate |  | partner-preference bias |
| Adoring | RELATIONSHIP | SOURCE | LOW | no | yes |  | love-attitude bias; high love bond |
| Affectionate | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | shows affection more; bond outcome; high bond |
| Agitating | PERSONALITY | SOURCE | LOW | no | innate |  | makes others angry |
| Agreeable | PERSONALITY | SOURCE | LOW | no | innate |  | easy-to-agree opinions |
| Aimless | PERSONALITY | TARGET | MEDIUM | no | yes |  | neglects study/exercise/club; delinquency outcome; neglect study/club |
| Ambusher | SEXUAL | TARGET | HIGH | no | yes |  | roams, rapes weaker chars; predator outcome; predator: high force-H count |
| Angry Sex | SEXUAL | TARGET | MEDIUM | no | yes |  | sex with hated people; sex w/ hated chars accrued |
| Apathetic | PERSONALITY | SOURCE | LOW | no | yes |  | weak feelings toward others; social isolation/neglect |
| Armed | COMBAT_VIOLENCE | TARGET | MEDIUM | yes | yes |  | "wins deadly confrontation"; combat status vs item-gate unclear; won deadly confrontation |
| Arrogant | PERSONALITY | SOURCE | LOW | no | innate |  | pride-based rejection |
| Assertive | SEXUAL | TARGET | LOW | no | yes |  | takes charge when initiating H; many H initiations |
| Attractive | STATS_TRAINING | TARGET | MEDIUM | yes | innate |  | doubles interaction success; stat-buff vs appearance |
| Auto Poser | META_SYSTEM | NONE | LOW | no | system |  | pose-loading utility |
| Baby Trap | PREGNANCY | TARGET | HIGH | no | yes |  | lures to impregnate self; pregnancy scheme; wants-kids + obsession |
| Bad Blood | META_SYSTEM | NONE | LOW | no | system |  | naming/enemy-group utility (global var) |
| Bad Luck Omen | PERSONALITY | SOURCE | LOW | no | innate |  | generic bad-luck aura |
| Banchou | STATUS_ROLE | GATE | HIGH | no | gate |  | role/milestone gate, not counter-driven |
| Battle Tactics | COMBAT_VIOLENCE | TARGET | MEDIUM | no | yes |  | post-fight effects by stance; training outcome; combat training |
| Begone Thot | PERSONALITY | SOURCE | LOW | no | innate |  | violent toward unwanted closeness |
| Bias-Abomination | PERSONALITY | SOURCE | LOW | no | yes | Abomination:BIAS | race-response bias; favorable experiences w/ abomination |
| Bias-Alien | PERSONALITY | SOURCE | LOW | no | yes | Alien:BIAS | race-response bias; favorable experiences w/ alien |
| Bias-Angel | PERSONALITY | SOURCE | LOW | no | yes | Angel:BIAS | race-response bias; favorable experiences w/ angel |
| Bias-Beastfolk | PERSONALITY | SOURCE | LOW | no | yes | Beastfolk:BIAS | race-response bias; favorable experiences w/ beastfolk |
| Bias-Construct | PERSONALITY | SOURCE | LOW | no | yes | Construct:BIAS | race-response bias; favorable experiences w/ construct |
| Bias-Deity | PERSONALITY | SOURCE | LOW | no | yes | Deity:BIAS | race-response bias; favorable experiences w/ deity |
| Bias-Demon | PERSONALITY | SOURCE | LOW | no | yes | Demon:BIAS | race-response bias; favorable experiences w/ demon |
| Bias-Dragon | PERSONALITY | SOURCE | LOW | no | yes | Dragon:BIAS | race-response bias; favorable experiences w/ dragon |
| Bias-Elf | PERSONALITY | SOURCE | LOW | no | yes | Elf:BIAS | race-response bias; favorable experiences w/ elf |
| Bias-Fairy | PERSONALITY | SOURCE | LOW | no | yes | Fairy:BIAS | race-response bias; favorable experiences w/ fairy |
| Bias-Ghost | PERSONALITY | SOURCE | LOW | no | yes | Ghost:BIAS | race-response bias; favorable experiences w/ ghost |
| Bias-Greenskin | PERSONALITY | SOURCE | LOW | no | yes | Greenskin:BIAS | race-response bias; favorable experiences w/ greenskin |
| Bias-Human | PERSONALITY | SOURCE | LOW | no | yes | Human:BIAS | race-response bias; favorable experiences w/ human |
| Bias-Inorganic | PERSONALITY | SOURCE | LOW | no | yes | Inorganic:BIAS | race-response bias; favorable experiences w/ inorganic |
| Bias-Machine | PERSONALITY | SOURCE | LOW | no | yes | Machine:BIAS | race-response bias; favorable experiences w/ machine |
| Bias-Magic | PERSONALITY | SOURCE | LOW | no | yes | Magic:BIAS | race-response bias; favorable experiences w/ magic |
| Bias-Meme | PERSONALITY | SOURCE | LOW | no | yes | Meme:BIAS | race-response bias; favorable experiences w/ meme |
| Bias-Mutant | PERSONALITY | SOURCE | LOW | no | yes | Mutant:BIAS | race-response bias; favorable experiences w/ mutant |
| Bias-Plant | PERSONALITY | SOURCE | LOW | no | yes | Plant:BIAS | race-response bias; favorable experiences w/ plant |
| Bias-Psychic | PERSONALITY | SOURCE | LOW | no | yes | Psychic:BIAS | race-response bias; favorable experiences w/ psychic |
| Bias-Spirit | PERSONALITY | SOURCE | LOW | no | yes | Spirit:BIAS | race-response bias; favorable experiences w/ spirit |
| Bias-Undead | PERSONALITY | SOURCE | LOW | no | yes | Undead:BIAS | race-response bias; favorable experiences w/ undead |
| Bias-Vampire | PERSONALITY | SOURCE | LOW | no | yes | Vampire:BIAS | race-response bias; favorable experiences w/ vampire |
| Bias-Zombie | PERSONALITY | SOURCE | LOW | no | yes | Zombie:BIAS | race-response bias; favorable experiences w/ zombie |
| Birthday Suit | SEXUAL | SOURCE | LOW | no | innate |  | strips immediately at H start |
| Blackmailer | BEHAVIOR_AI | TARGET | MEDIUM | yes | yes |  | exploits personal items; scheme vs role unclear; acquired blackmail item/circumstance |
| Body Conscious | PERSONALITY | SOURCE | LOW | no | innate |  | dislikes being seen naked |
| Boiling Point | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | repeated forced sex → snaps & murders; abuse outcome; repeated forced sex |
| Bookworm | STATS_TRAINING | TARGET | MEDIUM | no | yes |  | library-seeking; intelligence-leaning; high study counter |
| Breakup Style | APPEARANCE | NONE | LOW | no | system |  | style swap on breakup |
| Breast Envy | PERSONALITY | SOURCE | LOW | no | innate |  | envy of larger breasts |
| Brute | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | forces sex via unrefusable fight; predator outcome; predator: high force-H count |
| Bully | PERSONALITY | TARGET | MEDIUM | no | yes |  | bullies weaker disliked chars; dominance over weaker chars |
| Busy Hands | SEXUAL | TARGET | LOW | no | yes |  | always touching self; high arousal/addiction |
| Calculative | RELATIONSHIP | SOURCE | LOW | no | innate |  | won't break up without backup lover |
| Calming | PERSONALITY | SOURCE | LOW | no | innate |  | relaxes others |
| Capricious | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | unpredictable interaction results |
| Cat in Heat | SEXUAL | SOURCE | LOW | no | innate |  | horny on certain days |
| Cautious | BEHAVIOR_AI | SOURCE | LOW | no | yes |  | can't be slapped/caught off-guard; after being caught off-guard |
| Chained Maiden | SEXUAL | TARGET | HIGH | no | yes |  | enslaved to virginity-taker; possible H outcome; virginity taken by dominator |
| Charismatic | PERSONALITY | SOURCE | MEDIUM | no | innate |  | universally likeable |
| Chaste Cherisher | RELATIONSHIP | SOURCE | LOW | no | innate |  | likes high-virtue partners |
| Cheating | RELATIONSHIP | TARGET | HIGH | no | yes |  | prone to cheat; relationship-decay outcome; low loyalty + multiple suitors |
| Cheating Sheet | STATS_TRAINING | TARGET | LOW | no | yes |  | cheats on academic exam; low intelligence + exam pressure |
| Cheeky | PERSONALITY | SOURCE | LOW | no | innate |  | likes gloating |
| Cherry Hunter | SEXUAL | SOURCE | MEDIUM | no | innate |  | loves virgins; partner preference |
| Childhood Friend | RELATIONSHIP | SOURCE | LOW | no | system |  | preset friend bonds (global var) |
| Christian | SEXUAL | SOURCE | MEDIUM | no | innate |  | no vaginal sex before marriage |
| Chubby Chaser | SEXUAL | SOURCE | LOW | no | innate |  | prefers fat chars |
| Clique | RELATIONSHIP | SOURCE | LOW | no | innate |  | friendlier within named clique |
| Club Leader | STATUS_ROLE | GATE | HIGH | no | gate |  | role/milestone gate, not counter-driven |
| Club Pride | PERSONALITY | SOURCE | LOW | no | innate |  | won't change clubs |
| Club Style | APPEARANCE | NONE | LOW | no | system |  | style swap during club / corrupted |
| Coach | STATS_TRAINING | SOURCE | MEDIUM | no | yes |  | helps others with athletic training; high athletics |
| Cold Groin | SEXUAL | SOURCE | LOW | no | innate |  | won't have sex unless in mood |
| Compensated Dating | SEXUAL | TARGET | HIGH | no | yes |  | solicits sex at station; prostitution outcome; corruption + low status |
| Compliant | PERSONALITY | TARGET | MEDIUM | no | yes |  | complies with non-H force; submission outcome; repeated submission |
| Conflicted | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | may flip answers |
| Controlling | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | possessive of lover; possessive bond |
| Cool Sunglasses | APPEARANCE | NONE | LOW | yes | system |  | interaction bonus + item flavor; appearance vs stat |
| Corruption | PERSONALITY | TARGET | HIGH | no | yes |  | virtue loss/gain transforms style; core evo outcome; virtue loss |
| Corruptor | PERSONALITY | TARGET | HIGH | no | yes |  | corrupts others via force; agent of corruption; high corruption + force-H |
| Coward | COMBAT_VIOLENCE | SOURCE | LOW | no | innate |  | reluctant to fight stronger |
| Cowtits Craving | SEXUAL | SOURCE | LOW | no | innate |  | prefers large breasts |
| Credible | PERSONALITY | SOURCE | LOW | no | innate |  | trusted opinion |
| Crush | RELATIONSHIP | SOURCE | LOW | no | system |  | preset crush bonds (global var) |
| Cuck | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | watches lover with others; humiliation outcome; watched lover cheat repeatedly |
| Cupid | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | spreads good rumors to make love |
| Dark Semen | SEXUAL | TARGET | HIGH | no | yes |  | sex lowers partner morality; corruption agent; high corruption |
| Date Fashion | APPEARANCE | NONE | LOW | no | system |  | date-style swap |
| Decisive | RELATIONSHIP | SOURCE | LOW | no | innate |  | won't accept breakup refusal |
| Decoy Damsel | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | exploits White Knight |
| Degenerate | SEXUAL | SOURCE | LOW | no | innate |  | likes handholding (joke) |
| Delinquent | STATUS_ROLE | TARGET | HIGH | no | yes |  | trouble with authority; jail-relevant outcome; truancy + authority conflict |
| Demanding | RELATIONSHIP | SOURCE | LOW | no | innate |  | high lover expectations |
| Dense | RELATIONSHIP | SOURCE | LOW | no | innate |  | oblivious to confessions |
| Dependable | PERSONALITY | SOURCE | LOW | no | innate |  | helps those who ask |
| Depressing Dreams | PERSONALITY | SOURCE | LOW | no | innate |  | depressing dreams if naps |
| Depression | PERSONALITY | TARGET | HIGH | no | yes |  | 3-stage mood/stat debuff; clear evo outcome; social isolation/loss |
| Despises Midgets | PERSONALITY | SOURCE | LOW | no | innate |  | ignores short chars |
| Detective | STATUS_ROLE | GATE | HIGH | no | gate |  | role/milestone gate, not counter-driven |
| Devoted Spouse | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | loyal after marriage; post-marriage loyalty |
| Dicktator | SEXUAL | TARGET | MEDIUM | no | yes |  | forces transfer of sexual preference; high dominance/corruption |
| Dirty | SEXUAL | TARGET | MEDIUM | no | yes |  | stays covered in semen; high cum exposure |
| Discreet | SEXUAL | SOURCE | LOW | no | innate |  | prefers private sex |
| Dislikes Overly Competent | PERSONALITY | SOURCE | LOW | no | innate |  | dislikes very competent |
| Dislikes Simpletons | PERSONALITY | SOURCE | LOW | no | innate |  | dislikes the unintelligent |
| Diva | PERSONALITY | SOURCE | LOW | no | innate |  | starts with good impression |
| Dominant | SEXUAL | TARGET | MEDIUM | no | yes |  | prefers rough sex; many dominant H |
| Dominatrix | SEXUAL | TARGET | MEDIUM | no | yes |  | exploits masochists; femdom; dominance + masochist partners |
| Drama Queen | RELATIONSHIP | SOURCE | LOW | no | innate |  | creates relationship drama |
| Dreadful | PERSONALITY | SOURCE | MEDIUM | no | innate |  | dread aura; protects from rape, invites fights |
| Drunk | SEXUAL | SOURCE | LOW | no | innate |  | drinks → horny/responsive |
| Dry Skin | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | prefers pool location |
| Easy Victim | SEXUAL | TARGET | HIGH | no | yes |  | more likely rape target; victim outcome; repeated victimization |
| Embittered | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | bitter toward a gender after breakup; breakup w/ a gender |
| Emotional | PERSONALITY | SOURCE | LOW | no | innate |  | mood drives opinion shifts |
| Empathic | PERSONALITY | SOURCE | MEDIUM | no | innate |  | assimilates lover traits/values |
| Enemy | RELATIONSHIP | SOURCE | LOW | no | system |  | preset enemy bonds (global var) |
| Entitled | SEXUAL | TARGET | MEDIUM | no | yes |  | gets physical if refused; repeated refusal + force |
| Eris | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | spreads bad rumors to cause hate |
| Evening Cosplay | APPEARANCE | NONE | LOW | no | system |  | evening style swap |
| Evening Fashion | APPEARANCE | NONE | LOW | no | system |  | evening style swap |
| Exam Glasses | APPEARANCE | NONE | LOW | no | system |  | glasses during exam week |
| Fake Tits | APPEARANCE | SOURCE | LOW | no | innate |  | fake tits; grope mechanics |
| Family Guy | RELATIONSHIP | SOURCE | LOW | no | innate |  | won't love family (last name) |
| Family Guy 2 | RELATIONSHIP | SOURCE | LOW | no | innate |  | won't love family (first name) |
| Fashionable | APPEARANCE | NONE | LOW | no | system |  | daily random style |
| Fickle | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | dumps other lovers for new one; low loyalty |
| Final Solution | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | kills/forces to stay together if rejected; rejection + violence |
| Flaming Head | META_SYSTEM | NONE | LOW | yes | system |  | headpat burns clothes; gimmick, effect unclear |
| Flasher | SEXUAL | TARGET | MEDIUM | no | yes |  | flashes based on love/virtue; low virtue + high love |
| Flat Fancy | SEXUAL | SOURCE | LOW | no | innate |  | prefers small breasts |
| Flatter-proof | PERSONALITY | SOURCE | LOW | no | innate |  | dislikes flattery |
| Forceful | SEXUAL | TARGET | HIGH | no | yes |  | forces refusers to have sex; rapist outcome; predator: high force-H count |
| Forgetful | PERSONALITY | SOURCE | LOW | no | innate |  | forgets interactions/lover status |
| Forgiving | PERSONALITY | SOURCE | LOW | no | innate |  | accepts apologies |
| Fresh Laundry | APPEARANCE | NONE | LOW | no | system |  | resets style at home |
| Friendly Pat | RELATIONSHIP | SOURCE | LOW | no | innate |  | headpats seen as friendly |
| Futa Freak | SEXUAL | SOURCE | LOW | no | innate |  | prefers futanari |
| Futanari | SEXUAL | SOURCE | MEDIUM | no | innate |  | anatomy designation, not part of race prejudice/hostility axis |
| G Spot | SEXUAL | SOURCE | LOW | no | innate |  | massage arouses |
| Gambler | BEHAVIOR_AI | NONE | LOW | no | system |  | PC gamble minigame |
| Get On My Level | SEXUAL | SOURCE | LOW | no | innate |  | only sleeps with those who beat them |
| Gospel of Friendship | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | good rumors more effective |
| Gossip Lover | PERSONALITY | SOURCE | LOW | no | innate |  | agrees with rumors |
| Gossiper | RELATIONSHIP | TARGET | LOW | no | yes |  | spreads bad rumors when jealous; jealousy accrued |
| Gullible | PERSONALITY | SOURCE | MEDIUM | no | innate |  | doesn't suspect dark-place invites; rape-vuln |
| H Auto Poser | META_SYSTEM | NONE | LOW | no | system |  | H pose-loading utility |
| H Style | APPEARANCE | NONE | LOW | no | system |  | style swap at H start |
| Hates Slander | PERSONALITY | SOURCE | LOW | no | innate |  | dislikes malicious gossip |
| Haunted | META_SYSTEM | NONE | MEDIUM | yes | system |  | possession/body-swap mechanic; hard to map |
| Headpat Slut | SEXUAL | TARGET | LOW | no | yes |  | more susceptible to headpats; headpat conditioning |
| Henshin | APPEARANCE | NONE | LOW | no | system |  | PC transform-style key |
| Hesitant | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | may change their mind |
| Hidden Camera | BEHAVIOR_AI | SOURCE | LOW | yes | system |  | item-camera scheme; vague mechanical goal |
| Hoe Hopper | RELATIONSHIP | SOURCE | LOW | no | innate |  | likes low-virtue partners |
| Holy Semen | SEXUAL | TARGET | HIGH | no | yes |  | sex raises partner morality; purification agent; high virtue |
| Homewrecker | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | prefers taken people; corruption + cheating |
| Homophobic | PERSONALITY | SOURCE | LOW | no | innate |  | hates/fights homosexuals |
| Hot Body | COMBAT_VIOLENCE | SOURCE | LOW | no | innate |  | killers try different approach |
| Hug Pillow | RELATIONSHIP | TARGET | LOW | no | yes |  | more susceptible to hugs; hug conditioning |
| Human Guise | APPEARANCE | NONE | MEDIUM | yes | system |  | disguise-by-intelligence style system; complex |
| Hunter-Abomination | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Abomination:HOSTILE/hunter | hates abominations; trauma/abuse by abomination |
| Hunter-Alien | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Alien:HOSTILE/hunter | hates aliens; trauma/abuse by alien |
| Hunter-Angel | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Angel:HOSTILE/hunter | hates angels; trauma/abuse by angel |
| Hunter-Beastfolk | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Beastfolk:HOSTILE/hunter | hates beastfolk; trauma/abuse by beastfolk |
| Hunter-Construct | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Construct:HOSTILE/hunter | hates constructs; trauma/abuse by construct |
| Hunter-Deity | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Deity:HOSTILE/hunter | hates deities; trauma/abuse by deity |
| Hunter-Demon | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Demon:HOSTILE/hunter | hates demons; trauma/abuse by demon |
| Hunter-Dragon | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Dragon:HOSTILE/hunter | hates dragons; trauma/abuse by dragon |
| Hunter-Elf | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Elf:HOSTILE/hunter | hates elves; trauma/abuse by elf |
| Hunter-Fairy | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Fairy:HOSTILE/hunter | hates fairies; trauma/abuse by fairy |
| Hunter-Ghost | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Ghost:HOSTILE/hunter | hates ghosts; trauma/abuse by ghost |
| Hunter-Greenskin | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Greenskin:HOSTILE/hunter | hates greenskins; trauma/abuse by greenskin |
| Hunter-Human | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Human:HOSTILE/hunter | hates humans; trauma/abuse by human |
| Hunter-Inorganic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Inorganic:HOSTILE/hunter | hates inorganics; trauma/abuse by inorganic |
| Hunter-Machine | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Machine:HOSTILE/hunter | hates machines; trauma/abuse by machine |
| Hunter-Magic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Magic:HOSTILE/hunter | hates magic creatures; trauma/abuse by magic |
| Hunter-Meme | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Meme:HOSTILE/hunter | hates memes; trauma/abuse by meme |
| Hunter-Mutant | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Mutant:HOSTILE/hunter | hates mutants; trauma/abuse by mutant |
| Hunter-Plant | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Plant:HOSTILE/hunter | hates plants; trauma/abuse by plant |
| Hunter-Psychic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Psychic:HOSTILE/hunter | hates psychics; trauma/abuse by psychic |
| Hunter-Spirit | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Spirit:HOSTILE/hunter | hates spirits; trauma/abuse by spirit |
| Hunter-Undead | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Undead:HOSTILE/hunter | hates undead; trauma/abuse by undead |
| Hunter-Vampire | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Vampire:HOSTILE/hunter | hates vampires; trauma/abuse by vampire |
| Hunter-Zombie | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Zombie:HOSTILE/hunter | hates zombies; trauma/abuse by zombie |
| Impatient | PERSONALITY | TARGET | MEDIUM | no | yes |  | loses virtue if loves but no lover; love w/o lover |
| Inattentive | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | can't focus on topic |
| Incest Fetish | SEXUAL | SOURCE | LOW | no | innate |  | affectionate w/ family (last name) |
| Incest Fetish 2 | SEXUAL | SOURCE | LOW | no | innate |  | affectionate w/ family (first name) |
| Indifferent | RELATIONSHIP | SOURCE | LOW | no | innate |  | no interest in relationships |
| Infertile | PREGNANCY | GATE | MEDIUM | no | innate |  | cannot impregnate/conceive |
| Insane | PERSONALITY | TARGET | MEDIUM | no | yes |  | personality changes each action; extreme corruption/trauma |
| Insecure | PERSONALITY | TARGET | MEDIUM | no | yes |  | exploitable when weak; reversible; repeated weakening |
| Intimately Assertive | SEXUAL | TARGET | LOW | no | yes |  | asserts dominance in private; many private H |
| Introvert | PERSONALITY | SOURCE | LOW | no | innate |  | only approaches close people |
| Irregular Ovulation | PREGNANCY | SOURCE | MEDIUM | no | innate |  | normal days become risky |
| Irresponsible | PREGNANCY | SOURCE | LOW | no | innate |  | won't take pregnancy responsibility |
| Jaded | RELATIONSHIP | SOURCE | LOW | no | yes |  | dislikes romance; romantic disillusion |
| Jailer | STATUS_ROLE | GATE | HIGH | no | gate |  | role/milestone gate, not counter-driven |
| Kidnapper | SEXUAL | TARGET | HIGH | no | yes |  | blackmail-kidnap-rape scheme; predator outcome; predator scheme |
| Killer | COMBAT_VIOLENCE | GATE | HIGH | no | gate |  | role/milestone gate, not counter-driven |
| Killjoy | PERSONALITY | SOURCE | LOW | no | innate |  | dislikes happy people |
| Kink Suit | APPEARANCE | NONE | LOW | no | system |  | kinksuit style on command |
| Kleptomaniac | BEHAVIOR_AI | TARGET | LOW | no | yes |  | steals during commotion; theft during commotion |
| Klutz | APPEARANCE | SOURCE | LOW | no | innate |  | forgets to button clothes |
| Knife Magnet | COMBAT_VIOLENCE | TARGET | MEDIUM | no | yes |  | draws killer ire; victim outcome; targeted by killers |
| Knockup Chance | PREGNANCY | GATE | MEDIUM | no | system |  | chance-based impregnation system |
| Lightning Fingers | SEXUAL | TARGET | LOW | no | yes |  | gropes anyone; high arousal/addiction |
| Likes Quiet Places | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | prefers quiet rooms |
| Loathsome | PERSONALITY | SOURCE | LOW | no | innate |  | starts with bad impression |
| LOVE OF YOUR LIFE | RELATIONSHIP | SOURCE | LOW | no | system |  | single soulmate lock |
| Lover Solidarity | RELATIONSHIP | SOURCE | LOW | no | innate |  | hates lover's enemies |
| Loving | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | passive love gain to lovers; high love bond |
| Loving Bully | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | bullies weaker loved ones; love + dominance over weaker |
| Low Endurance | SEXUAL | SOURCE | LOW | no | innate |  | H once per day |
| Low Self-Esteem | PERSONALITY | TARGET | MEDIUM | no | yes |  | grumbly/apologetic; self-worth outcome; repeated failure/abuse |
| Loyal | RELATIONSHIP | TARGET | HIGH | no | yes |  | exclusive; avoids suitors; loyalty outcome; sustained exclusive bond |
| Lucky Sukebe | APPEARANCE | NONE | LOW | no | system |  | skirt-lift gag |
| Magnetic Tits | SEXUAL | TARGET | LOW | no | yes |  | more susceptible to groping; grope conditioning |
| Maneater | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | may kill non-lover sex partner; kill + non-lover H |
| Marriage | RELATIONSHIP | GATE | HIGH | no | gate |  | role/milestone gate, not counter-driven |
| Martial Artist | COMBAT_VIOLENCE | TARGET | MEDIUM | no | yes |  | adaptive fighting stance; combat training |
| Martial Arts Prodigy | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | training outcome; jail martial-training reward; high combat training |
| Martial Loser | COMBAT_VIOLENCE | TARGET | MEDIUM | no | yes |  | bad at fighting; negative outcome; repeated combat losses |
| Mary | SEXUAL | SOURCE | MEDIUM | no | innate |  | always regains virginity |
| Mass Murderer | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | tries to kill nightly; high kill count |
| Masseuse | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | offers massages more |
| Medium Appreciator | SEXUAL | SOURCE | LOW | no | innate |  | prefers medium breasts |
| Mind Before Matter | COMBAT_VIOLENCE | SOURCE | MEDIUM | no | yes |  | fights with intelligence not strength; high intelligence build |
| Mind Control | SEXUAL | GATE | MEDIUM | no | system |  | PC forces exploitable/dumb chars into H |
| Misanthrope | PERSONALITY | TARGET | MEDIUM | no | yes |  | passively gains hate for everyone; accumulated hate |
| Monogamous | RELATIONSHIP | SOURCE | MEDIUM | no | innate |  | no multiple relationships |
| Moody | PERSONALITY | SOURCE | LOW | no | innate |  | unpredictable mood swings |
| Murderous | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | willing to kill a lot; high kill willingness |
| Musclehead | STATS_TRAINING | TARGET | MEDIUM | no | yes |  | loves exercising; strength-leaning; high exercise counter |
| Must Protecc | BEHAVIOR_AI | SOURCE | MEDIUM | no | innate |  | bystanders rescue when abused |
| Naive | PERSONALITY | SOURCE | MEDIUM | no | innate |  | trusts everyone; rape-vuln |
| Narcissistic | PERSONALITY | SOURCE | LOW | no | innate |  | thinks self best |
| Narcoleptic | PERSONALITY | SOURCE | MEDIUM | no | innate |  | suggestible when relaxed; rape-vuln |
| Natural Enemy-Abomination | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Abomination:HOSTILE/natenemy | strong vs abominations; combat conditioning vs abomination |
| Natural Enemy-Alien | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Alien:HOSTILE/natenemy | strong vs aliens; combat conditioning vs alien |
| Natural Enemy-Angel | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Angel:HOSTILE/natenemy | strong vs angels; combat conditioning vs angel |
| Natural Enemy-Beastfolk | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Beastfolk:HOSTILE/natenemy | strong vs beastfolk; combat conditioning vs beastfolk |
| Natural Enemy-Construct | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Construct:HOSTILE/natenemy | strong vs constructs; combat conditioning vs construct |
| Natural Enemy-Deity | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Deity:HOSTILE/natenemy | strong vs deities; combat conditioning vs deity |
| Natural Enemy-Demon | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Demon:HOSTILE/natenemy | strong vs demons; combat conditioning vs demon |
| Natural Enemy-Dragon | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Dragon:HOSTILE/natenemy | strong vs dragons; combat conditioning vs dragon |
| Natural Enemy-Elf | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Elf:HOSTILE/natenemy | strong vs elves; combat conditioning vs elf |
| Natural Enemy-Fairy | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Fairy:HOSTILE/natenemy | strong vs fairies; combat conditioning vs fairy |
| Natural Enemy-Ghost | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Ghost:HOSTILE/natenemy | strong vs ghosts; combat conditioning vs ghost |
| Natural Enemy-Greenskin | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Greenskin:HOSTILE/natenemy | strong vs greenskins; combat conditioning vs greenskin |
| Natural Enemy-Human | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Human:HOSTILE/natenemy | strong vs humans; combat conditioning vs human |
| Natural Enemy-Inorganic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Inorganic:HOSTILE/natenemy | strong vs inorganics; combat conditioning vs inorganic |
| Natural Enemy-Machine | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Machine:HOSTILE/natenemy | strong vs machines; combat conditioning vs machine |
| Natural Enemy-Magic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Magic:HOSTILE/natenemy | strong vs magic creatures; combat conditioning vs magic |
| Natural Enemy-Meme | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Meme:HOSTILE/natenemy | strong vs memes; combat conditioning vs meme |
| Natural Enemy-Mutant | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Mutant:HOSTILE/natenemy | strong vs mutants; combat conditioning vs mutant |
| Natural Enemy-Plant | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Plant:HOSTILE/natenemy | strong vs plants; combat conditioning vs plant |
| Natural Enemy-Psychic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Psychic:HOSTILE/natenemy | strong vs psychics; combat conditioning vs psychic |
| Natural Enemy-Spirit | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Spirit:HOSTILE/natenemy | strong vs spirits; combat conditioning vs spirit |
| Natural Enemy-Undead | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Undead:HOSTILE/natenemy | strong vs undead; combat conditioning vs undead |
| Natural Enemy-Vampire | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Vampire:HOSTILE/natenemy | strong vs vampires; combat conditioning vs vampire |
| Natural Enemy-Zombie | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Zombie:HOSTILE/natenemy | strong vs zombies; combat conditioning vs zombie |
| Naughty | SEXUAL | TARGET | MEDIUM | no | yes |  | more susceptible to lewd when aroused; high arousal accrued |
| Neck Biter | SEXUAL | TARGET | MEDIUM | no | yes |  | bites neck, drains strength on kiss; vampiric H conditioning |
| Nine Lives | META_SYSTEM | NONE | LOW | no | system |  | style swap instead of death |
| No Bullshit | COMBAT_VIOLENCE | SOURCE | LOW | no | innate |  | kills those who fake deafness |
| Not For Lewding | SEXUAL | GATE | MEDIUM | no | system |  | cannot consent to sex |
| Observant | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | adapts to mood; detects cheating |
| Obsession-Abomination | RELATIONSHIP | SOURCE | LOW | no | yes | Abomination:OBSESSION | loves abominations; repeated H/love w/ abomination |
| Obsession-Alien | RELATIONSHIP | SOURCE | LOW | no | yes | Alien:OBSESSION | loves aliens; repeated H/love w/ alien |
| Obsession-Angel | RELATIONSHIP | SOURCE | LOW | no | yes | Angel:OBSESSION | loves angels; repeated H/love w/ angel |
| Obsession-Beastfolk | RELATIONSHIP | SOURCE | LOW | no | yes | Beastfolk:OBSESSION | loves beastfolk; repeated H/love w/ beastfolk |
| Obsession-Construct | RELATIONSHIP | SOURCE | LOW | no | yes | Construct:OBSESSION | loves constructs; repeated H/love w/ construct |
| Obsession-Deity | RELATIONSHIP | SOURCE | LOW | no | yes | Deity:OBSESSION | loves deities; repeated H/love w/ deity |
| Obsession-Demon | RELATIONSHIP | SOURCE | LOW | no | yes | Demon:OBSESSION | loves demons; repeated H/love w/ demon |
| Obsession-Dragon | RELATIONSHIP | SOURCE | LOW | no | yes | Dragon:OBSESSION | loves dragons; repeated H/love w/ dragon |
| Obsession-Elf | RELATIONSHIP | SOURCE | LOW | no | yes | Elf:OBSESSION | loves elves; repeated H/love w/ elf |
| Obsession-Fairy | RELATIONSHIP | SOURCE | LOW | no | yes | Fairy:OBSESSION | loves fairies; repeated H/love w/ fairy |
| Obsession-Ghost | RELATIONSHIP | SOURCE | LOW | no | yes | Ghost:OBSESSION | loves ghosts; repeated H/love w/ ghost |
| Obsession-Greenskin | RELATIONSHIP | SOURCE | LOW | no | yes | Greenskin:OBSESSION | loves greenskins; repeated H/love w/ greenskin |
| Obsession-Human | RELATIONSHIP | SOURCE | LOW | no | yes | Human:OBSESSION | loves humans; repeated H/love w/ human |
| Obsession-Inorganic | RELATIONSHIP | SOURCE | LOW | no | yes | Inorganic:OBSESSION | loves inorganics; repeated H/love w/ inorganic |
| Obsession-Machine | RELATIONSHIP | SOURCE | LOW | no | yes | Machine:OBSESSION | loves machines; repeated H/love w/ machine |
| Obsession-Magic | RELATIONSHIP | SOURCE | LOW | no | yes | Magic:OBSESSION | loves magic creatures; repeated H/love w/ magic |
| Obsession-Meme | RELATIONSHIP | SOURCE | LOW | no | yes | Meme:OBSESSION | loves memes; repeated H/love w/ meme |
| Obsession-Mutant | RELATIONSHIP | SOURCE | LOW | no | yes | Mutant:OBSESSION | loves mutants; repeated H/love w/ mutant |
| Obsession-Plant | RELATIONSHIP | SOURCE | LOW | no | yes | Plant:OBSESSION | loves plants; repeated H/love w/ plant |
| Obsession-Psychic | RELATIONSHIP | SOURCE | LOW | no | yes | Psychic:OBSESSION | loves psychics; repeated H/love w/ psychic |
| Obsession-Spirit | RELATIONSHIP | SOURCE | LOW | no | yes | Spirit:OBSESSION | loves spirits; repeated H/love w/ spirit |
| Obsession-Undead | RELATIONSHIP | SOURCE | LOW | no | yes | Undead:OBSESSION | loves undead; repeated H/love w/ undead |
| Obsession-Vampire | RELATIONSHIP | SOURCE | LOW | no | yes | Vampire:OBSESSION | loves vampires; repeated H/love w/ vampire |
| Obsession-Zombie | RELATIONSHIP | SOURCE | LOW | no | yes | Zombie:OBSESSION | loves zombies; repeated H/love w/ zombie |
| On a Diet | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | refuses eating interactions |
| Pacifist | COMBAT_VIOLENCE | SOURCE | MEDIUM | no | innate |  | avoids violence |
| Painful Periods | SEXUAL | SOURCE | LOW | no | innate |  | won't hold hands certain days |
| Panty Thief | SEXUAL | TARGET | MEDIUM | no | yes |  | raids lockers when horny; high arousal + theft |
| Paranoid | PERSONALITY | SOURCE | LOW | no | yes |  | hides when threatened; repeated threats |
| Peacemaker | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | reconciles cold-attitude chars |
| Perfectly Average | STATS_TRAINING | SOURCE | LOW | no | innate |  | stats gravitate to class average |
| Petty | PERSONALITY | SOURCE | LOW | no | innate |  | easily offended; spreads rumors |
| Pheromones | SEXUAL | SOURCE | MEDIUM | no | innate |  | unnaturally arousing |
| Philophobic | RELATIONSHIP | SOURCE | MEDIUM | no | yes |  | won't love/confess/date; romantic trauma |
| Photophobic | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | sensitive to light outside |
| Picky | SEXUAL | SOURCE | LOW | no | innate |  | prefers similar-preference partners |
| Pillow Princess | SEXUAL | NONE | LOW | no | system |  | H-AI on by default (PC) |
| Polyamorous | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | doesn't mind lover sleeping around; low jealousy + multiple lovers |
| Possessive | RELATIONSHIP | TARGET | MEDIUM | no | yes |  | drives off lover's suitors; possessive bond |
| Praying Mantis | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | eats sex partner after H; predator: kill-after-H |
| Prefers Average Size | SEXUAL | SOURCE | LOW | no | innate |  | prefers normal height |
| Prefers Fun-size | SEXUAL | SOURCE | LOW | no | innate |  | prefers short |
| Prefers Jumbo-size | SEXUAL | SOURCE | LOW | no | innate |  | prefers tall |
| Pregnancy | PREGNANCY | GATE | HIGH | no | system |  | core pregnancy overhaul system |
| Prejudice-Abomination | PERSONALITY | SOURCE | LOW | no | yes | Abomination:PREJUDICE | less responsive to abominations; dominated/wronged by abomination |
| Prejudice-Alien | PERSONALITY | SOURCE | LOW | no | yes | Alien:PREJUDICE | less responsive to aliens; dominated/wronged by alien |
| Prejudice-Angel | PERSONALITY | SOURCE | LOW | no | yes | Angel:PREJUDICE | less responsive to angels; dominated/wronged by angel |
| Prejudice-Beastfolk | PERSONALITY | SOURCE | LOW | no | yes | Beastfolk:PREJUDICE | less responsive to beastfolk; dominated/wronged by beastfolk |
| Prejudice-Construct | PERSONALITY | SOURCE | LOW | no | yes | Construct:PREJUDICE | less responsive to constructs; dominated/wronged by construct |
| Prejudice-Deity | PERSONALITY | SOURCE | LOW | no | yes | Deity:PREJUDICE | less responsive to deities; dominated/wronged by deity |
| Prejudice-Demons | PERSONALITY | SOURCE | LOW | no | yes | Demon:PREJUDICE | less responsive to demons; dominated/wronged by demon |
| Prejudice-Dragon | PERSONALITY | SOURCE | LOW | no | yes | Dragon:PREJUDICE | less responsive to dragons; dominated/wronged by dragon |
| Prejudice-Elf | PERSONALITY | SOURCE | LOW | no | yes | Elf:PREJUDICE | less responsive to elves; dominated/wronged by elf |
| Prejudice-Fairy | PERSONALITY | SOURCE | LOW | no | yes | Fairy:PREJUDICE | less responsive to fairies; dominated/wronged by fairy |
| Prejudice-Ghost | PERSONALITY | SOURCE | LOW | no | yes | Ghost:PREJUDICE | less responsive to ghosts; dominated/wronged by ghost |
| Prejudice-Greenskin | PERSONALITY | SOURCE | LOW | no | yes | Greenskin:PREJUDICE | less responsive to greenskins; dominated/wronged by greenskin |
| Prejudice-Human | PERSONALITY | SOURCE | LOW | no | yes | Human:PREJUDICE | less responsive to humans; dominated/wronged by human |
| Prejudice-Inorganic | PERSONALITY | SOURCE | LOW | no | yes | Inorganic:PREJUDICE | less responsive to inorganics; dominated/wronged by inorganic |
| Prejudice-Machine | PERSONALITY | SOURCE | LOW | no | yes | Machine:PREJUDICE | less responsive to machines; dominated/wronged by machine |
| Prejudice-Magic | PERSONALITY | SOURCE | LOW | no | yes | Magic:PREJUDICE | less responsive to magic creatures; dominated/wronged by magic |
| Prejudice-Meme | PERSONALITY | SOURCE | LOW | no | yes | Meme:PREJUDICE | less responsive to memes; dominated/wronged by meme |
| Prejudice-Mutant | PERSONALITY | SOURCE | LOW | no | yes | Mutant:PREJUDICE | less responsive to mutants; dominated/wronged by mutant |
| Prejudice-Plant | PERSONALITY | SOURCE | LOW | no | yes | Plant:PREJUDICE | less responsive to plants; dominated/wronged by plant |
| Prejudice-Psychic | PERSONALITY | SOURCE | LOW | no | yes | Psychic:PREJUDICE | less responsive to psychics; dominated/wronged by psychic |
| Prejudice-Spirit | PERSONALITY | SOURCE | LOW | no | yes | Spirit:PREJUDICE | less responsive to spirits; dominated/wronged by spirit |
| Prejudice-Undead | PERSONALITY | SOURCE | LOW | no | yes | Undead:PREJUDICE | less responsive to undead; dominated/wronged by undead |
| Prejudice-Vampire | PERSONALITY | SOURCE | LOW | no | yes | Vampire:PREJUDICE | less responsive to vampires; dominated/wronged by vampire |
| Prejudice-Zombie | PERSONALITY | SOURCE | LOW | no | yes | Zombie:PREJUDICE | less responsive to zombies; dominated/wronged by zombie |
| Profane | PERSONALITY | TARGET | HIGH | no | yes |  | corrupts via sex/force; strong corruption agent; high corruption + force-H |
| Puritan | PERSONALITY | TARGET | MEDIUM | no | yes |  | reprimands public sex; high-virtue outcome; high virtue |
| Race-Abomination | STATUS_ROLE | SOURCE | LOW | no | innate | Abomination:DESIGNATION | race designation; race designation (born as) |
| Race-Alien | STATUS_ROLE | SOURCE | LOW | no | innate | Alien:DESIGNATION | race designation; race designation (born as) |
| Race-Angel | STATUS_ROLE | SOURCE | LOW | no | innate | Angel:DESIGNATION | race designation; race designation (born as) |
| Race-Beastfolk | STATUS_ROLE | SOURCE | LOW | no | innate | Beastfolk:DESIGNATION | race designation; race designation (born as) |
| Race-Construct | STATUS_ROLE | SOURCE | LOW | no | innate | Construct:DESIGNATION | race designation; race designation (born as) |
| Race-Deity | STATUS_ROLE | SOURCE | LOW | no | innate | Deity:DESIGNATION | race designation; race designation (born as) |
| Race-Demon | STATUS_ROLE | SOURCE | LOW | no | innate | Demon:DESIGNATION | race designation; race designation (born as) |
| Race-Dragon | STATUS_ROLE | SOURCE | LOW | no | innate | Dragon:DESIGNATION | race designation; race designation (born as) |
| Race-Elf | STATUS_ROLE | SOURCE | LOW | no | innate | Elf:DESIGNATION | race designation; race designation (born as) |
| Race-Fairy | STATUS_ROLE | SOURCE | LOW | no | innate | Fairy:DESIGNATION | race designation; race designation (born as) |
| Race-Ghost | STATUS_ROLE | SOURCE | LOW | no | innate | Ghost:DESIGNATION | race designation; race designation (born as) |
| Race-Greenskin | STATUS_ROLE | SOURCE | LOW | no | innate | Greenskin:DESIGNATION | race designation; race designation (born as) |
| Race-Human | STATUS_ROLE | SOURCE | LOW | no | innate | Human:DESIGNATION | race designation; race designation (born as) |
| Race-Inorganic | STATUS_ROLE | SOURCE | LOW | no | innate | Inorganic:DESIGNATION | race designation; race designation (born as) |
| Race-Machine | STATUS_ROLE | SOURCE | LOW | no | innate | Machine:DESIGNATION | race designation; race designation (born as) |
| Race-Magic | STATUS_ROLE | SOURCE | LOW | no | innate | Magic:DESIGNATION | race designation; race designation (born as) |
| Race-Meme | STATUS_ROLE | SOURCE | LOW | no | innate | Meme:DESIGNATION | race designation; race designation (born as) |
| Race-Mutant | STATUS_ROLE | SOURCE | LOW | no | innate | Mutant:DESIGNATION | race designation; race designation (born as) |
| Race-Plant | STATUS_ROLE | SOURCE | LOW | no | innate | Plant:DESIGNATION | race designation; race designation (born as) |
| Race-Psychic | STATUS_ROLE | SOURCE | LOW | no | innate | Psychic:DESIGNATION | race designation; race designation (born as) |
| Race-Spirit | STATUS_ROLE | SOURCE | LOW | no | innate | Spirit:DESIGNATION | race designation; race designation (born as) |
| Race-Undead | STATUS_ROLE | SOURCE | LOW | no | innate | Undead:DESIGNATION | race designation; race designation (born as) |
| Race-Vampire | STATUS_ROLE | SOURCE | LOW | no | innate | Vampire:DESIGNATION | race designation; race designation (born as) |
| Race-Zombie | STATUS_ROLE | SOURCE | LOW | no | innate | Zombie:DESIGNATION | race designation; race designation (born as) |
| Resentful | PERSONALITY | SOURCE | LOW | no | innate |  | holds grudges |
| Respects Moderacy | RELATIONSHIP | SOURCE | LOW | no | innate |  | likes normal-virtue partners |
| Rival | RELATIONSHIP | SOURCE | LOW | no | system |  | preset rival bonds (global var) |
| Routine Fashion | APPEARANCE | NONE | LOW | no | system |  | daily cycling style |
| Sadist | PERSONALITY | TARGET | MEDIUM | no | yes |  | gains love from bullying; love from bullying accrued |
| Safe Sex | SEXUAL | SOURCE | MEDIUM | no | innate |  | always uses protection |
| Saint | PERSONALITY | TARGET | HIGH | no | yes |  | blessings, mitigates corruption; purity agent; very high virtue |
| Seducer | PERSONALITY | TARGET | HIGH | no | yes |  | corrupts via romance; high corruption + romance |
| Semen Demon | SEXUAL | TARGET | HIGH | no | yes |  | seeks cum when aroused; addiction-like; high cum/H counters |
| Sentimental | RELATIONSHIP | SOURCE | LOW | no | innate |  | likes holders of their friend item |
| Serial Killer | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | kills targeted attribute nightly; high kill count |
| Serial Smoocher | SEXUAL | TARGET | MEDIUM | no | yes |  | nonconsensual serial kissing; high kiss counter |
| Sex Addict | SEXUAL | TARGET | HIGH | no | yes |  | loses virtue without sex; canonical evo outcome; high cum/H counters |
| Sex Crazed | SEXUAL | TARGET | HIGH | no | yes |  | rapes when aroused; predator outcome; high arousal + force-H |
| Sex Hater | SEXUAL | SOURCE | MEDIUM | no | yes |  | hates sex/erotic activity; H trauma / very high virtue |
| Sexually Confused | SEXUAL | TARGET | MEDIUM | no | yes |  | orientation shifts by flirt gender; mixed-gender flirting |
| Shaming | COMBAT_VIOLENCE | TARGET | MEDIUM | no | yes |  | strips opponent in fight/rape; fight/rape dominance |
| Significant Other | RELATIONSHIP | SOURCE | LOW | no | system |  | preset lover bonds (global var) |
| Skinwalker | META_SYSTEM | NONE | MEDIUM | yes | system |  | disguise/possession witch; mechanics unclear |
| Slayer-Abomination | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Abomination:HOSTILE/slayer | can kill abominations; combat conditioning vs abomination |
| Slayer-Alien | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Alien:HOSTILE/slayer | can kill aliens; combat conditioning vs alien |
| Slayer-Angel | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Angel:HOSTILE/slayer | can kill angels; combat conditioning vs angel |
| Slayer-Beastfolk | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Beastfolk:HOSTILE/slayer | can kill beastfolk; combat conditioning vs beastfolk |
| Slayer-Construct | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Construct:HOSTILE/slayer | can kill constructs; combat conditioning vs construct |
| Slayer-Deity | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Deity:HOSTILE/slayer | can kill deities; combat conditioning vs deity |
| Slayer-Demon | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Demon:HOSTILE/slayer | can kill demons; combat conditioning vs demon |
| Slayer-Dragon | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Dragon:HOSTILE/slayer | can kill dragons; combat conditioning vs dragon |
| Slayer-Elf | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Elf:HOSTILE/slayer | can kill elves; combat conditioning vs elf |
| Slayer-Fairy | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Fairy:HOSTILE/slayer | can kill fairies; combat conditioning vs fairy |
| Slayer-Ghost | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Ghost:HOSTILE/slayer | can kill ghosts; combat conditioning vs ghost |
| Slayer-Greenskin | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Greenskin:HOSTILE/slayer | can kill greenskins; combat conditioning vs greenskin |
| Slayer-Human | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Human:HOSTILE/slayer | can kill humans; combat conditioning vs human |
| Slayer-Inorganic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Inorganic:HOSTILE/slayer | can kill inorganics; combat conditioning vs inorganic |
| Slayer-Machine | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Machine:HOSTILE/slayer | can kill machines; combat conditioning vs machine |
| Slayer-Magic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Magic:HOSTILE/slayer | can kill magic creatures; combat conditioning vs magic |
| Slayer-Meme | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Meme:HOSTILE/slayer | can kill memes; combat conditioning vs meme |
| Slayer-Mutant | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Mutant:HOSTILE/slayer | can kill mutants; combat conditioning vs mutant |
| Slayer-Plant | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Plant:HOSTILE/slayer | can kill plants; combat conditioning vs plant |
| Slayer-Psychic | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Psychic:HOSTILE/slayer | can kill psychics; combat conditioning vs psychic |
| Slayer-Spirit | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Spirit:HOSTILE/slayer | can kill spirits; combat conditioning vs spirit |
| Slayer-Undead | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Undead:HOSTILE/slayer | can kill undead; combat conditioning vs undead |
| Slayer-Vampire | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Vampire:HOSTILE/slayer | can kill vampires; combat conditioning vs vampire |
| Slayer-Zombie | COMBAT_VIOLENCE | SOURCE | LOW | no | yes | Zombie:HOSTILE/slayer | can kill zombies; combat conditioning vs zombie |
| Sleepyhead | APPEARANCE | NONE | LOW | no | system |  | morning style; resets on headpat |
| Slim Striker | SEXUAL | SOURCE | LOW | no | innate |  | prefers thin chars |
| Snobbish | RELATIONSHIP | SOURCE | LOW | no | innate |  | won't date unpopular |
| Sport Style | APPEARANCE | NONE | LOW | no | system |  | sports style / corrupted |
| Stage Fright | STATS_TRAINING | SOURCE | LOW | no | innate |  | performs worse in exams |
| Stalker | BEHAVIOR_AI | TARGET | MEDIUM | no | yes |  | follows people; may approach in private; obsession bond |
| Star-struck | RELATIONSHIP | SOURCE | LOW | no | innate |  | admires popular chars |
| Sticky Cum | SEXUAL | SOURCE | LOW | no | innate |  | cum persists until washed |
| Stubborn | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | needs "no" twice |
| Studious | STATS_TRAINING | TARGET | MEDIUM | no | yes |  | loves studying; intelligence-leaning; high study counter |
| Succubus | SEXUAL | TARGET | HIGH | no | yes |  | gains strength via sex; supernatural outcome; strength-via-sex accrued |
| Sugar Lips | SEXUAL | TARGET | LOW | no | yes |  | more susceptible to kisses; kiss conditioning |
| Sugar Rush | BEHAVIOR_AI | SOURCE | LOW | no | innate |  | sleepy until eats |
| Summoner | COMBAT_VIOLENCE | GATE | MEDIUM | yes | system |  | demon-summon ritual; sacrifice mechanic, complex |
| Sunday Cosplay | APPEARANCE | NONE | LOW | no | system |  | Sunday cosplay style |
| Sunday Fashion | APPEARANCE | NONE | LOW | no | system |  | Sunday style swap |
| Swift Hands | SEXUAL | SOURCE | LOW | no | system |  | undress via gropes (PC) |
| Swimsuit Style | APPEARANCE | NONE | LOW | no | system |  | swimsuit style / corrupted |
| Teacher Style | APPEARANCE | NONE | LOW | no | system |  | teacher-seat default style |
| Teacher Thirsty | SEXUAL | SOURCE | LOW | no | innate |  | likes teachers |
| Thief | BEHAVIOR_AI | TARGET | LOW | no | yes |  | steals via touches/massages; theft via touches accrued |
| Thorough | COMBAT_VIOLENCE | SOURCE | MEDIUM | no | yes |  | murder unseen avoids arrest; murder-evasion conditioning |
| Thot Patrol | PERSONALITY | TARGET | MEDIUM | no | yes |  | beats up low-virtue people; high virtue + dominance |
| Toilet Police | PERSONALITY | SOURCE | LOW | no | innate |  | enforces correct toilet |
| Tone-deaf | STATS_TRAINING | SOURCE | LOW | no | innate |  | bad at singing |
| Totally Random | META_SYSTEM | NONE | LOW | no | system |  | randomizes personality/stats/traits on add |
| Trend Follower | PERSONALITY | SOURCE | LOW | no | innate |  | opinion follows class consensus |
| Truancy | STATUS_ROLE | TARGET | HIGH | no | yes |  | skips school; delinquency/jail-relevant; skipped-school counter |
| Tutor | STATS_TRAINING | SOURCE | MEDIUM | no | yes |  | helps others academically; high intelligence |
| Ugly | STATS_TRAINING | TARGET | MEDIUM | yes | yes |  | halves interaction success; appearance vs stat; neglect/weight/grooming |
| Unchivalrous | SEXUAL | TARGET | MEDIUM | no | yes |  | takes refusal badly; repeated refusals taken badly |
| Uncredible | PERSONALITY | SOURCE | LOW | no | innate |  | distrusted opinion |
| Under Pressure Perfomance | STATS_TRAINING | SOURCE | LOW | no | innate |  | performs better in exams |
| Undying | META_SYSTEM | GATE | LOW | yes | system |  | "does not die"; status flag, no detail |
| Unlikely Confidence | SEXUAL | SOURCE | MEDIUM | no | innate |  | can avoid being forced by stat diff |
| Unlovable | RELATIONSHIP | SOURCE | LOW | no | innate |  | can't be more than friend |
| Values Perfect Measurements | SEXUAL | SOURCE | LOW | no | innate |  | prefers normal figure |
| Vengeful | COMBAT_VIOLENCE | TARGET | MEDIUM | no | yes |  | avenges killed loved one; loved one killed |
| Vigilante | COMBAT_VIOLENCE | TARGET | MEDIUM | no | yes |  | stops murderers; witnessed murders |
| Virtuous | RELATIONSHIP | SOURCE | MEDIUM | no | innate |  | refuses non-serious daters |
| Vivid Imagination | SEXUAL | NONE | LOW | no | system |  | PC sex-scene imagination |
| Voice of the Sirens | PERSONALITY | SOURCE | MEDIUM | no | innate |  | voice makes people fall in love |
| Voyeur | SEXUAL | NONE | LOW | no | system |  | PC spectate-couple action |
| Wants Kids | PREGNANCY | TARGET | HIGH | no | yes |  | happy to have unprotected risky sex; high love + maternal |
| Wary | BEHAVIOR_AI | SOURCE | MEDIUM | no | yes |  | senses danger; hesitant to interact; repeated danger exposure |
| Weight Issues | APPEARANCE | TARGET | MEDIUM | no | yes |  | weight-driven appearance shift; lifestyle outcome; diet/exercise neglect |
| Whimsical | PERSONALITY | TARGET | MEDIUM | no | yes |  | changes prefs/virtue/orientation each action; instability/corruption |
| White Knight | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | fights to protect rape victims; jail-relevant; witnessed rape victims |
| Wimp | PERSONALITY | TARGET | MEDIUM | no | yes |  | can't refuse liked person's lewd/romantic; repeated coercion |
| Yandere Type A | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | kills cheating lover; obsessive love + betrayal |
| Yandere Type B | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | kills the one lover cheats with; obsessive love + betrayal |
| Yandere Type C | COMBAT_VIOLENCE | TARGET | HIGH | no | yes |  | may kill people lover dislikes; obsessive love + betrayal |

## RACE SUBSYSTEM

The racial-evolution axis. Every race below carries the SAME five valences, each backed by a module
family. This is the vocabulary for the racial-evolution rules: a character's standing toward a race
can shift based on who dominated/wronged/loved them.

### Valence vocabulary (module family → valence → developable)

| valence | module family(ies) | meaning | developable | example driver |
|---|---|---|---|---|
| DESIGNATION | `Race-X` | this char IS race X | innate | on card from creation |
| BIAS | `Bias-X` | more responsive/positive toward X | yes | favorable experiences with X |
| PREJUDICE | `Prejudice-X` | less responsive/negative toward X | yes | dominated/wronged by X |
| HOSTILE | `Hunter-X`, `Natural Enemy-X`, `Slayer-X` | wants to harm/kill X | yes | trauma/abuse by X; combat conditioning vs X |
| OBSESSION | `Obsession-X` | fixated on / loves X | yes | repeated H/love with X |

HOSTILE is no longer a single flat valence — it is a three-tier **escalation ladder**, recorded in
the `race` column via a sub-tag (`X:HOSTILE/<tier>`):

| tier | module family | sub-tag | meaning |
|---|---|---|---|
| 1 | `Hunter-X` | `X:HOSTILE/hunter` | emotional hatred of X |
| 2 | `Natural Enemy-X` | `X:HOSTILE/natenemy` | combat-strong vs X |
| 3 | `Slayer-X` | `X:HOSTILE/slayer` | lethal capability vs X |

All three HOSTILE tiers stay `developable: yes`. Pick the tier by HOW the hostility manifests
(hatred → combat advantage → lethal capability) and how far it has escalated.

### Escalation ladder (full racial-standing axis)

A character's standing toward a race moves along this axis in two directions:

- **Negative:** `neutral -> PREJUDICE -> HOSTILE/hunter -> HOSTILE/natenemy -> HOSTILE/slayer`
  (wronged/dominated → emotional hatred → combat-conditioned → lethal). Driven by sustained
  abuse/domination and combat conditioning against the race.
- **Positive:** `neutral -> BIAS -> OBSESSION`
  (favorable experiences → fixation/love). Driven by repeated positive/loving H with the race.

`DESIGNATION` (`Race-X`) sits outside the axis — it is who you are, not a standing.

### Racial-evolution rule pattern

Every valence except DESIGNATION is `developable`. A character is driven along the racial axis by
accumulated relationship/domination state, e.g.:
- A non-Human repeatedly dominated/raped by a Human → develops `Human:PREJUDICE`, escalating to
  `Human:HOSTILE` (Hunter-Human) under sustained abuse.
- A character with many positive/loving H encounters with Demons → `Demon:BIAS`, escalating to
  `Demon:OBSESSION`.
- Combat conditioning / repeatedly fighting a race → `X:HOSTILE` (Natural Enemy / Slayer).
Only `Race-X` (DESIGNATION) is innate — you are born your race; the rest are earned standings.

### The 24 races

All 24 races have the full valence set (1 DESIGNATION + 1 BIAS + 1 PREJUDICE + 3 HOSTILE + 1
OBSESSION = 7 modules each → 168 race-subsystem modules). DESIGNATION is `innate`; all other 6 per
race are `developable: yes`.

Races: **Abomination, Alien, Angel, Beastfolk, Construct, Deity, Demon, Dragon, Elf, Fairy, Ghost,
Greenskin, Human, Inorganic, Machine, Magic, Meme, Mutant, Plant, Psychic, Spirit, Undead, Vampire,
Zombie.**

Per race, the modules are:

The HOSTILE column lists all three escalation-tier families (Hunter = `/hunter`, Natural Enemy =
`/natenemy`, Slayer = `/slayer`); each maps to `X:HOSTILE/<tier>` in the `race` column.

| Race | DESIGNATION (innate) | BIAS (dev) | PREJUDICE (dev) | HOSTILE tiers: Hunter/NatEnemy/Slayer (dev) | OBSESSION (dev) |
|---|---|---|---|---|---|
| Abomination | Race-Abomination | Bias-Abomination | Prejudice-Abomination | Hunter/Natural Enemy/Slayer-Abomination | Obsession-Abomination |
| Alien | Race-Alien | Bias-Alien | Prejudice-Alien | Hunter/Natural Enemy/Slayer-Alien | Obsession-Alien |
| Angel | Race-Angel | Bias-Angel | Prejudice-Angel | Hunter/Natural Enemy/Slayer-Angel | Obsession-Angel |
| Beastfolk | Race-Beastfolk | Bias-Beastfolk | Prejudice-Beastfolk | Hunter/Natural Enemy/Slayer-Beastfolk | Obsession-Beastfolk |
| Construct | Race-Construct | Bias-Construct | Prejudice-Construct | Hunter/Natural Enemy/Slayer-Construct | Obsession-Construct |
| Deity | Race-Deity | Bias-Deity | Prejudice-Deity | Hunter/Natural Enemy/Slayer-Deity | Obsession-Deity |
| Demon | Race-Demon | Bias-Demon | Prejudice-Demons* | Hunter/Natural Enemy/Slayer-Demon | Obsession-Demon |
| Dragon | Race-Dragon | Bias-Dragon | Prejudice-Dragon | Hunter/Natural Enemy/Slayer-Dragon | Obsession-Dragon |
| Elf | Race-Elf | Bias-Elf | Prejudice-Elf | Hunter/Natural Enemy/Slayer-Elf | Obsession-Elf |
| Fairy | Race-Fairy | Bias-Fairy | Prejudice-Fairy | Hunter/Natural Enemy/Slayer-Fairy | Obsession-Fairy |
| Ghost | Race-Ghost | Bias-Ghost | Prejudice-Ghost | Hunter/Natural Enemy/Slayer-Ghost | Obsession-Ghost |
| Greenskin | Race-Greenskin | Bias-Greenskin | Prejudice-Greenskin | Hunter/Natural Enemy/Slayer-Greenskin | Obsession-Greenskin |
| Human | Race-Human | Bias-Human | Prejudice-Human | Hunter/Natural Enemy/Slayer-Human | Obsession-Human |
| Inorganic | Race-Inorganic | Bias-Inorganic | Prejudice-Inorganic | Hunter/Natural Enemy/Slayer-Inorganic | Obsession-Inorganic |
| Machine | Race-Machine | Bias-Machine | Prejudice-Machine | Hunter/Natural Enemy/Slayer-Machine | Obsession-Machine |
| Magic | Race-Magic | Bias-Magic | Prejudice-Magic | Hunter/Natural Enemy/Slayer-Magic | Obsession-Magic |
| Meme | Race-Meme | Bias-Meme | Prejudice-Meme | Hunter/Natural Enemy/Slayer-Meme | Obsession-Meme |
| Mutant | Race-Mutant | Bias-Mutant | Prejudice-Mutant | Hunter/Natural Enemy/Slayer-Mutant | Obsession-Mutant |
| Plant | Race-Plant | Bias-Plant | Prejudice-Plant | Hunter/Natural Enemy/Slayer-Plant | Obsession-Plant |
| Psychic | Race-Psychic | Bias-Psychic | Prejudice-Psychic | Hunter/Natural Enemy/Slayer-Psychic | Obsession-Psychic |
| Spirit | Race-Spirit | Bias-Spirit | Prejudice-Spirit | Hunter/Natural Enemy/Slayer-Spirit | Obsession-Spirit |
| Undead | Race-Undead | Bias-Undead | Prejudice-Undead | Hunter/Natural Enemy/Slayer-Undead | Obsession-Undead |
| Vampire | Race-Vampire | Bias-Vampire | Prejudice-Vampire | Hunter/Natural Enemy/Slayer-Vampire | Obsession-Vampire |
| Zombie | Race-Zombie | Bias-Zombie | Prejudice-Zombie | Hunter/Natural Enemy/Slayer-Zombie | Obsession-Zombie |

\* Naming inconsistency in source: the prejudice module for Demon is `Prejudice-Demons` (plural),
while Bias/Hunter/Slayer/Natural Enemy/Obsession/Race use singular `Demon`. Mapped to `Demon`.

### Related but NOT in the `race` column (race-adjacent designations)

- **Futanari** — an anatomy designation (H-role + pregnancy-compat), not a race-standing dynamic.
  Resolved: it stays OUT of the race subsystem axis, with an empty `race` cell and `developable:
  innate`. Note in the table reads "anatomy designation, not part of race prejudice/hostility axis".
  It is not part of the PREJUDICE/HOSTILE/BIAS/OBSESSION standing axis and is never folded into a
  `Futanari:DESIGNATION` valence.
- **Vampire/Zombie/etc. behavior modules** (e.g. Neck Biter, Succubus) describe race-flavored
  behavior but are not part of the race-standing subsystem; they are categorized as SEXUAL outcomes,
  not `race` cells.

## UNCERTAIN — for joint review

### COMBAT_VIOLENCE
- **Armed** — "Will win in a deadly confrontation." Unclear whether this is a combat-status TARGET outcome or an item/equipment GATE flag (analogous to "is armed with a weapon").
- **Summoner** — Demon-summon ritual requiring a loved-one sacrifice. Spans relationship/combat/meta; complex multi-step mechanic that is hard to map to a single state threshold. Tagged GATE as an unlockable ability but debatable.

### SEXUAL
- (none beyond cross-listed) 

### BEHAVIOR_AI
- **Blackmailer** — Exploits possession of someone's personal sexual item. Could be a behavioral scheme (BEHAVIOR_AI) or a status/role; whether it's an assignable outcome vs. a card-setup trait is debatable.
- **Hidden Camera** — Items contain hidden cameras used "for goals beyond any real importance." Mechanical effect is vague/joke-like; unclear what it actually drives.

### APPEARANCE / STATS_TRAINING
- **Attractive** — Doubles interaction success. Mechanically a stat/social buff but framed as physical attractiveness; function (STATS_TRAINING vs APPEARANCE) is debatable, and whether it's an assignable TARGET vs base SOURCE trait is unclear.
- **Ugly** — Halves interaction success. Same ambiguity as Attractive (appearance vs stat; outcome vs base trait).
- **Cool Sunglasses** — Daytime interaction bonus plus evening misfire from obscured vision. Item-flavored; appearance vs stat-buff classification is unclear.

### META_SYSTEM / STATUS
- **Flaming Head** — Headpat burns clothes off and sends griefer to infirmary. Gag/gimmick; actual mechanical effect and whether it belongs to any character-state domain is unclear.
- **Haunted** — Phantom possession with separate play data and body-swapping. Powerful meta mechanic that doesn't fit a clean state→module mapping; review whether it should ever be auto-assigned.
- **Skinwalker** — Disguise/possession witch; description is lore-only with no concrete mechanics listed in the catalog.
- **Human Guise** — Style changes based on observer intelligence (disguise system). Primarily APPEARANCE but functions as a hidden-identity mechanic; review whether it's evolution-relevant.
- **Undying** — "Does not die." No scope tag and no detail; presumably a status GATE flag but effect/extent unconfirmed.

## Counts

### Per function
- SEXUAL — 75
- PERSONALITY — 113
- RELATIONSHIP — 69
- STATUS_ROLE — 30
- STATS_TRAINING — 12
- PREGNANCY — 7
- BEHAVIOR_AI — 26
- APPEARANCE — 24
- COMBAT_VIOLENCE — 101
- META_SYSTEM — 9

(Total: 466)

### Per evo_role
- TARGET — 104
- GATE — 13
- SOURCE — 316
- NONE — 33

(Total: 466)

### Uncertain
- Flagged uncertain: 12

### Per developable
- yes (driven by accumulated DB state; dual innate-or-earned) — 259
- innate (starting trait/designation only) — 154
- gate (assigned by role/milestone event at a world/status transition, not counter-driven) — 6
  (Jailer, Detective, Banchou, Club Leader, Marriage, Killer)
- system (meta/utility/cosmetic) — 47

(Total: 466)

### Race subsystem
- Races: 24 (Abomination, Alien, Angel, Beastfolk, Construct, Deity, Demon, Dragon, Elf, Fairy,
  Ghost, Greenskin, Human, Inorganic, Machine, Magic, Meme, Mutant, Plant, Psychic, Spirit, Undead,
  Vampire, Zombie)
- Valences per race: 5 (DESIGNATION, BIAS, PREJUDICE, HOSTILE, OBSESSION); HOSTILE splits into 3
  escalation tiers (`/hunter`, `/natenemy`, `/slayer`)
- Race-subsystem modules: 168 (7 per race = 1 Race + 1 Bias + 1 Prejudice + 3 Hostile families + 1
  Obsession)
- HOSTILE rows carrying a tier sub-tag in the `race` column: 72 (24 races × 3 tiers); all
  `developable: yes`
- Of those: 24 innate (DESIGNATION) + 144 developable (all other valences)
- Race-adjacent designation outside the `race` column: Futanari (1, innate; resolved — anatomy
  designation, not part of the race standing axis)
