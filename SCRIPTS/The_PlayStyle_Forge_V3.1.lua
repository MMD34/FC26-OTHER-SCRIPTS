-- ============================================================
-- [[ FC26 THE PLAYSTYLE FORGE - V3 (MASTERCLASS EVOLVED) ]]
-- ============================================================

require 'imports/other/helpers'
require 'imports/other/playstyles_enum'

-- Polyfill for math.tanh (missing in some Lua 5.3+ environments)
if not math.tanh then
    function math.tanh(x)
        if x > 20 then return 1.0 end
        if x < -20 then return -1.0 end
        local e = math.exp(2 * x)
        return (e - 1) / (e + 1)
    end
end

math.randomseed(os.time())

-- ╔════════════════════════════════════════════════════════════╗
-- ║                      >>> USER CONFIG <<<
-- ║  ONLY CHANGE THE VALUE BELOW IF YOU WANT TO DO A DRY RUN
-- ║  THEN EXECUTE THE SCRIPT
-- ╚════════════════════════════════════════════════════════════╝
local USER_CONFIG = {
    DRY_RUN        = false     -- <<< true = dry run | false = apply changes
}
-- ╔════════════════════════════════════════════════════════════╗
-- ║           >>> CONFIG END <<<
-- ║  DO NOT CHANGE ANYTHING BELOW THIS LINE
-- ╚════════════════════════════════════════════════════════════╝

-- Dynamic Team ID detection via Live Editor API
local USER_TEAM_ID = GetUserTeamID()
if not USER_TEAM_ID or USER_TEAM_ID <= 0 then
    MessageBox("The PlayStyle Forge V3 (Engine V14.1) - ERROR",
        "Unable to detect your team ID automatically!\n\n"
        .. "Make sure you have loaded a Career Mode save\n"
        .. "and are managing a team before executing this script.\n\n"
        .. "No changes have been made.")
    return
end

-- ============================================================
-- REGLAGES DE SEUILS
-- ============================================================
local ELITE_PS_THRESHOLD = 85
local ORGANIC_UNLOCK_THRESHOLD = 82
local AUDIT_KEEP_THRESHOLD = 65

-- ============================================================
-- CONFIGURATION DNA V14.1
-- ============================================================
local CFG = {
    -- AXE 1 : Sigmoïde logistique (remplace quadratique + MAX_POOL_SCORE)
    SIGMOID_L            = 200,    -- asymptote haute (score max naturel)
    SIGMOID_K            = 0.35,   -- pente (sensibilité autour du point d'inflexion)
    SIGMOID_OFFSET       = 12,     -- x₀ = threshold + offset

    -- AXE 2 : Spécialiste exponentiel continu
    SPECIALIST_ALPHA     = 120,    -- B(T1) = 120
    SPECIALIST_BETA      = 0.1897, -- ln(800/120)/10
    SPECIALIST_T1        = 85,     -- seuil d'activation

    -- AXE 3 : Moyenne harmonique (puissance p)
    HARMONIC_P           = -1,     -- p=-1 = harmonique classique

    -- AXE 4 : Sigmoïde prérequis
    PREREQ_LAMBDA_FACTOR = 5,      -- λ = 5/(soft-hard), (Sprint 4 recalibration)

    -- AXE 5 : Synergies logarithmiques
    SYNERGY_GAMMA        = 12,     -- facteur d'échelle
    SYNERGY_TAU          = 80,     -- constante de normalisation
    SYNERGY_THRESHOLD    = 80,     -- score source minimum

    -- AXE 6 : Gaussienne d'âge
    AGE_MAX_BONUS        = 8,      -- A_max
    AGE_SPEED_MU         = 24,     -- pic pour PS vitesse
    AGE_SPEED_SIGMA      = 4,
    AGE_READ_MU          = 30,     -- pic pour PS lecture
    AGE_READ_SIGMA       = 5,

    -- AXE 7 : Accumulation bornée additive (remplace norme L2)
    -- cap · tanh(Σ / cap) — rendements décroissants mais récompense la compétence large
    POOL_CAP             = 400,    -- asymptote du pool (Sprint 1 fix)

    -- AXE 8 : Bruit gaussien
    NOISE_ENABLED        = true,
    NOISE_TRUNCATE_SIGMA = 2,      -- tronquer à ±2σ

    -- AXE 9 : Softmax température
    SOFTMAX_TAU          = 15,

    -- Off-role
    OFFROLE_PENALTY      = 0.4,
    OFFROLE_MAX          = 2,

    -- Shooting guarantee
    SHOOTING_MIN         = 2,

    -- Height thresholds
    HEIGHT_MIN_AERIAL    = 180,
    HEIGHT_MIN_HEADER    = 175,

    -- Audit
    AUDIT_MAX_RETAINED   = 3,
    AUDIT_FLEX_DECAY     = 0.7,    -- AXE 12 : multiplicateur pour PS flex audité
    AUDIT_OFFROLE_DECAY  = 0.3,    -- AXE 12 : multiplicateur pour PS off-role audité

    -- Organic unlock dynamic threshold (AXE 10c)
    ORGANIC_BASE_THRESHOLD = 82,
    ORGANIC_POOL_REF       = 10,   -- taille de pool de référence
    ORGANIC_POOL_ADJUST    = 0.5,  -- ajustement par unité d'écart

    -- PS+ Merit Gate (Improvement Plan — replaces raw pool score for Elite gate)
    PS_PLUS_TECH_THRESHOLD = 82,   -- minimum calc_technical_base_v14 score to qualify
                                   -- (in stat space [0,100]; ≈ dominant stat of ~85)
    PS_PLUS_BASE_FLOOR     = 80,   -- minimum entry.base (peak raw stat) to qualify
                                   -- (blocks synergy/archetype inflation with no raw backing)
    PS_PLUS_WEIGHT_TECH    = 0.70, -- weight of technical base in composite merit score
    PS_PLUS_WEIGHT_BASE    = 0.30, -- weight of raw base in composite merit score
                                   -- (weights must sum to 1.0)
}

local SHOOTING_PS = {
    ENUM_PLAYSTYLE1_FINESSE_SHOT,
    ENUM_PLAYSTYLE1_POWER_SHOT,
    ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT,
    ENUM_PLAYSTYLE1_CHIP_SHOT,
    ENUM_PLAYSTYLE1_GAMECHANGER
}

local SHOOTING_POSITIONS = {ST = true, WING = true, CAM = true}
local ROLE_BOOST = 300
local SHOOTING_BOOST = 250

local function get_limits(ovr, pot)
    local limit, plus_limit
    if ovr >= 90 then limit, plus_limit = 10, 4
    elseif ovr >= 87 then limit, plus_limit = 9, 3
    elseif ovr >= 84 then limit, plus_limit = 8, 3
    elseif ovr >= 81 then limit, plus_limit = 7, 2
    elseif ovr >= 78 then limit, plus_limit = 6, 2
    elseif ovr >= 75 then limit, plus_limit = 5, 1
    elseif ovr >= 72 then limit, plus_limit = 4, 1
    elseif ovr >= 69 then limit, plus_limit = 3, 1
    else limit, plus_limit = 2, 1 end

    if pot >= 85 and (pot - ovr) >= 8 then
        plus_limit = math.min(4, plus_limit + 1)
    end
    return limit, plus_limit
end

-- ============================================================
-- AXE 1 : SIGMOÏDE LOGISTIQUE PARAMÉTRÉE
-- Remplace stat_score quadratique + MAX_POOL_SCORE
-- S(x) = L / (1 + e^(-k * (x - x₀)))
-- Calibré : S(threshold) ≈ 0, S(threshold+10) ≈ L/2, S(threshold+20) ≈ 0.95L
-- ============================================================
local function stat_score_sigmoid(val, threshold)
    if val <= threshold then return 0 end
    local x0 = threshold + CFG.SIGMOID_OFFSET
    local raw = CFG.SIGMOID_L / (1 + math.exp(-CFG.SIGMOID_K * (val - x0)))
    -- Normaliser pour que S(threshold) = 0
    local floor_val = CFG.SIGMOID_L / (1 + math.exp(-CFG.SIGMOID_K * (threshold - x0)))
    return math.max(0, math.floor(raw - floor_val))
end

-- ============================================================
-- AXE 2 : SPÉCIALISTE EXPONENTIEL CONTINU
-- B(x) = α · e^(β · (x - T₁))  pour x ≥ T₁
-- Calibré : B(85)=120, B(90)≈309, B(95)=800
-- ============================================================
local function specialist_bonus(stat_val)
    if stat_val < CFG.SPECIALIST_T1 then return 0 end
    return math.floor(CFG.SPECIALIST_ALPHA * math.exp(CFG.SPECIALIST_BETA * (stat_val - CFG.SPECIALIST_T1)))
end

-- ============================================================
-- AXE 3 : MOYENNE HARMONIQUE PONDÉRÉE (Generalized Mean, p=-1)
-- H_w = (Σ wᵢ) / (Σ wᵢ/xᵢ)
-- Pénalise naturellement les valeurs faibles
-- ============================================================
local function generalized_mean(values, weights, p)
    p = p or CFG.HARMONIC_P
    local n = #values
    if n == 0 then return 0 end

    -- Protection contre les valeurs nulles/négatives
    local safe_values = {}
    local safe_weights = {}
    local total_w = 0
    for i = 1, n do
        local v = math.max(1, values[i] or 1)  -- clamp minimum à 1
        local w = (weights and weights[i]) or 1
        safe_values[i] = v
        safe_weights[i] = w
        total_w = total_w + w
    end
    if total_w == 0 then return 0 end

    if p == 0 then
        -- Cas limite : moyenne géométrique
        local log_sum = 0
        for i = 1, n do
            log_sum = log_sum + safe_weights[i] * math.log(safe_values[i])
        end
        return math.exp(log_sum / total_w)
    end

    local sum = 0
    for i = 1, n do
        sum = sum + safe_weights[i] * (safe_values[i] ^ p)
    end
    return (sum / total_w) ^ (1 / p)
end

local function harmonic_mean(...)
    local vals = {...}
    return generalized_mean(vals, nil, -1)
end

-- ============================================================
-- AXE 4 : PRÉREQUIS SIGMOÏDAUX CONTINUS
-- μ(x) = 1 / (1 + e^(-λ · (x - midpoint)))
-- λ = 6/(soft-hard), midpoint = (hard+soft)/2
-- μ(hard) ≈ 0.05, μ(soft) ≈ 0.95
-- ============================================================
local function prereq_sigmoid(val, hard, soft)
    if soft <= hard then
        -- Dégénéré : fallback binaire
        if val >= hard then return 1.0 else return 0.0 end
    end
    local midpoint = (hard + soft) / 2
    local lambda = CFG.PREREQ_LAMBDA_FACTOR / (soft - hard)
    return 1 / (1 + math.exp(-lambda * (val - midpoint)))
end

-- ============================================================
-- AXE 5 : SYNERGIES LOGARITHMIQUES PROPORTIONNELLES
-- bonus(src) = γ · ln(1 + src / τ)
-- ============================================================
local function synergy_transfer(source_score)
    if source_score < CFG.SYNERGY_THRESHOLD then return 0 end
    return math.floor(CFG.SYNERGY_GAMMA * math.log(1 + source_score / CFG.SYNERGY_TAU))
end

-- ============================================================
-- AXE 6 : GAUSSIENNE D'ÂGE PAR CATÉGORIE
-- A(age) = A_max · e^(-(age - μ)² / (2σ²))
-- Centré au pic, décroissance naturelle des deux côtés
-- ============================================================
local SPEED_PS = {
    ENUM_PLAYSTYLE1_RAPID, ENUM_PLAYSTYLE1_QUICK_STEP, ENUM_PLAYSTYLE1_TRICKSTER,
    ENUM_PLAYSTYLE1_TECHNICAL, ENUM_PLAYSTYLE1_ACROBATIC
}
local READ_PS = {
    ENUM_PLAYSTYLE1_ANTICIPATE, ENUM_PLAYSTYLE1_FIRST_TOUCH, ENUM_PLAYSTYLE1_INCISIVE_PASS,
    ENUM_PLAYSTYLE1_JOCKEY, ENUM_PLAYSTYLE1_TIKI_TAKA, ENUM_PLAYSTYLE1_INTERCEPT,
    ENUM_PLAYSTYLE1_INVENTIVE, ENUM_PLAYSTYLE1_ENFORCER
}

local function contains(tbl, val)
    for _, v in ipairs(tbl) do if v == val then return true end end
    return false
end

local function gaussian(x, mu, sigma)
    return math.exp(-((x - mu) ^ 2) / (2 * sigma * sigma))
end

local function age_bonus_gaussian(age, ps_id)
    if not age or age <= 0 then return 0 end

    if contains(SPEED_PS, ps_id) then
        return math.floor(CFG.AGE_MAX_BONUS * gaussian(age, CFG.AGE_SPEED_MU, CFG.AGE_SPEED_SIGMA))
    elseif contains(READ_PS, ps_id) then
        return math.floor(CFG.AGE_MAX_BONUS * gaussian(age, CFG.AGE_READ_MU, CFG.AGE_READ_SIGMA))
    end
    return 0
end

-- ============================================================
-- AXE 8 : BRUIT GAUSSIEN TRONQUÉ (Box-Muller)
-- ============================================================
local function gaussian_noise(mean, stddev)
    if not CFG.NOISE_ENABLED or stddev <= 0 then return 0 end
    local u1 = math.max(1e-10, math.random())  -- éviter log(0)
    local u2 = math.random()
    local z = math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)
    -- Tronquer à ±TRUNCATE_SIGMA
    z = math.max(-CFG.NOISE_TRUNCATE_SIGMA, math.min(CFG.NOISE_TRUNCATE_SIGMA, z))
    return math.floor(mean + z * stddev + 0.5)
end

local function proportional_noise_v14(val, comp)
    if not CFG.NOISE_ENABLED then return 0 end
    local base_stddev = math.max(0.5, (val - 60) * 0.03)
    -- Composure module la variance : haute composure = faible variance
    local comp_factor = 1.2 - (comp or 50) / 100
    local stddev = base_stddev * math.max(0.3, comp_factor)
    -- AXE 8 : Amplification ×5 (Sprint 5) pour rendre le bruit significatif
    return gaussian_noise(0, stddev * 5)
end

-- ============================================================
-- AXE 9 : SOFTMAX PONDÉRÉ POUR BASES TECHNIQUES
-- T = Σ wᵢ · xᵢ · softmax(xᵢ/τ)
-- La stat la plus forte domine, les secondaires contribuent
-- ============================================================
local function softmax_weighted(values, tau)
    tau = tau or CFG.SOFTMAX_TAU
    local n = #values
    if n == 0 then return 0 end
    if n == 1 then return values[1] end

    -- Stabilisation numérique : soustraire le max
    local max_val = -math.huge
    for i = 1, n do
        if values[i] > max_val then max_val = values[i] end
    end

    local exp_sum = 0
    local exps = {}
    for i = 1, n do
        exps[i] = math.exp((values[i] - max_val) / tau)
        exp_sum = exp_sum + exps[i]
    end

    local result = 0
    for i = 1, n do
        local weight = exps[i] / exp_sum
        result = result + weight * values[i]
    end
    return result
end

-- ============================================================
-- SYSTÈME DE PRÉREQUIS V14.1 (AXE 4 - Sigmoïdal continu)
-- ============================================================
local P_PREREQS = {
    [ENUM_PLAYSTYLE1_FINESSE_SHOT]     = {stat="fin",   hard=70, soft=80, alt="cur", alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_CHIP_SHOT]        = {stat="fin",   hard=72, soft=82, alt="bcon", alt_hard=65, alt_soft=78},
    [ENUM_PLAYSTYLE1_POWER_SHOT]       = {stat="shpow", hard=72, soft=82, alt="fin",  alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT]  = {stat="shpow", hard=70, soft=80, alt="fin",  alt_hard=65, alt_soft=75},

    [ENUM_PLAYSTYLE1_ACROBATIC]        = {stat="agi", hard=75, soft=83, alt="vol", alt_hard=70, alt_soft=80},
    [ENUM_PLAYSTYLE1_GAMECHANGER]      = {stat="fin", hard=65, soft=75, alt="cur", alt_hard=60, alt_soft=70, mode="require_all"},
    [ENUM_PLAYSTYLE1_DEAD_BALL]        = {stat="fka", hard=68, soft=78, alt="shpow", alt_hard=62, alt_soft=72},

    [ENUM_PLAYSTYLE1_TIKI_TAKA]        = {stat="pas", hard=73, soft=83},
    [ENUM_PLAYSTYLE1_INCISIVE_PASS]    = {stat="pas", hard=72, soft=82, alt="vis", alt_hard=68, alt_soft=78},
    [ENUM_PLAYSTYLE1_PINGED_PASS]      = {stat="lpa", hard=72, soft=82, alt="vis", alt_hard=68, alt_soft=78},
    [ENUM_PLAYSTYLE1_LONG_BALL_PASS]   = {stat="lpa", hard=70, soft=80, alt="vis", alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_WHIPPED_PASS]     = {stat="crs", hard=70, soft=82, alt="cur", alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_INVENTIVE]        = {stat="vis", hard=70, soft=82, alt="pas", alt_hard=65, alt_soft=75},

    [ENUM_PLAYSTYLE1_TRICKSTER]        = {stat="dri", hard=75, soft=82, alt="agi", alt_hard=72, alt_soft=80},
    [ENUM_PLAYSTYLE1_TECHNICAL]        = {stat="dri", hard=75, soft=83},
    [ENUM_PLAYSTYLE1_PRESS_PROVEN]     = {stat="dri", hard=78, soft=86, alt="comp", alt_hard=70, alt_soft=80},

    [ENUM_PLAYSTYLE1_RAPID]            = {stat="spd", hard=76, soft=84},
    [ENUM_PLAYSTYLE1_QUICK_STEP]       = {stat="acc", hard=78, soft=86},
    [ENUM_PLAYSTYLE1_INTERCEPT]        = {stat="icp", hard=70, soft=80, alt="rea", alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_ANTICIPATE]       = {stat="defaw", hard=70, soft=80, alt="icp", alt_hard=65, alt_soft=75},

    [ENUM_PLAYSTYLE1_JOCKEY]           = {stat="defaw", hard=68, soft=78, alt="agi", alt_hard=62, alt_soft=72},
    [ENUM_PLAYSTYLE1_BLOCK]            = {stat="stntk", hard=70, soft=80, alt="rea", alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_SLIDE_TACKLE]     = {stat="slitp", hard=70, soft=80, alt="stntk", alt_hard=65, alt_soft=75},

    [ENUM_PLAYSTYLE1_BRUISER]          = {stat="str", hard=76, soft=86},
    [ENUM_PLAYSTYLE1_ENFORCER]         = {stat="str", hard=76, soft=84, alt="agg", alt_hard=70, alt_soft=80},
    [ENUM_PLAYSTYLE1_LONG_THROW]       = {stat="str", hard=70, soft=80, alt="lpa", alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_RELENTLESS]       = {stat="sta", hard=76, soft=86},

    [ENUM_PLAYSTYLE1_FIRST_TOUCH]      = {stat="bcon", hard=70, soft=80, alt="rea", alt_hard=65, alt_soft=75},
    [ENUM_PLAYSTYLE1_AERIAL_FORTRESS]  = {stat="hea", hard=68, soft=74},
    [ENUM_PLAYSTYLE1_PRECISION_HEADER] = {stat="hea", hard=65, soft=74},
}

-- AXE 4 : Application continue des prérequis
local function apply_prereqs_filter_v14(pool, sc)
    for ps_id, entry in pairs(pool) do
        local prereq = P_PREREQS[ps_id]
        if prereq and entry and entry.score and entry.score > 0 then
            local main_val = sc[prereq.stat] or 0
            local mu_main = prereq_sigmoid(main_val, prereq.hard, prereq.soft)

            local mu_combined
            if prereq.alt then
                local alt_val = sc[prereq.alt] or 0
                local alt_hard = prereq.alt_hard or prereq.hard
                local alt_soft = prereq.alt_soft or prereq.soft
                local mu_alt = prereq_sigmoid(alt_val, alt_hard, alt_soft)

                if prereq.mode == "require_all" then
                    -- T-norme produit : les deux doivent être satisfaits
                    mu_combined = mu_main * mu_alt
                else
                    -- AXE 4 : Łukasiewicz t-norm (Sprint 4)
                    -- max(0, mu1 + mu2 - 1) — requires meaningful presence of both
                    mu_combined = math.max(0, mu_main + mu_alt - 1)
                end
            else
                mu_combined = mu_main
            end

            -- Appliquer l'atténuation continue
            entry.score = math.floor(entry.score * mu_combined)
            entry.prereq_mu = mu_combined -- AXE 10g : Store for validation (Sprint 7)
        end
    end
end

-- ============================================================
-- STAT -> PLAYSTYLE map (scanner multi-source)
-- ============================================================
local STAT_TO_PS_MAP = {
    fin  = {{ENUM_PLAYSTYLE1_FINESSE_SHOT,70}, {ENUM_PLAYSTYLE1_CHIP_SHOT,72}, {ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT,70}, {ENUM_PLAYSTYLE1_GAMECHANGER,65}},
    dri  = {{ENUM_PLAYSTYLE1_TECHNICAL,75}, {ENUM_PLAYSTYLE1_TRICKSTER,72}, {ENUM_PLAYSTYLE1_FIRST_TOUCH,70}, {ENUM_PLAYSTYLE1_PRESS_PROVEN,72}},
    icp  = {{ENUM_PLAYSTYLE1_INTERCEPT,70}, {ENUM_PLAYSTYLE1_ANTICIPATE,68}},
    pas  = {{ENUM_PLAYSTYLE1_TIKI_TAKA,73}, {ENUM_PLAYSTYLE1_INCISIVE_PASS,72}, {ENUM_PLAYSTYLE1_INVENTIVE,74}},
    lpa  = {{ENUM_PLAYSTYLE1_PINGED_PASS,72}, {ENUM_PLAYSTYLE1_LONG_BALL_PASS,70}},
    crs  = {{ENUM_PLAYSTYLE1_WHIPPED_PASS,70}},
    spd  = {{ENUM_PLAYSTYLE1_RAPID,76}},
    acc  = {{ENUM_PLAYSTYLE1_QUICK_STEP,78}, {ENUM_PLAYSTYLE1_RAPID,76}},
    str  = {{ENUM_PLAYSTYLE1_BRUISER,76}, {ENUM_PLAYSTYLE1_ENFORCER,76}, {ENUM_PLAYSTYLE1_LONG_THROW,70}, {ENUM_PLAYSTYLE1_POWER_SHOT,70}, {ENUM_PLAYSTYLE1_PRESS_PROVEN,72}},
    sta  = {{ENUM_PLAYSTYLE1_RELENTLESS,76}, {ENUM_PLAYSTYLE1_PRESS_PROVEN,72}},
    hea  = {{ENUM_PLAYSTYLE1_AERIAL_FORTRESS,70}, {ENUM_PLAYSTYLE1_PRECISION_HEADER,68}},
    shpow = {{ENUM_PLAYSTYLE1_POWER_SHOT,70}},
    agi   = {{ENUM_PLAYSTYLE1_ACROBATIC,75}, {ENUM_PLAYSTYLE1_QUICK_STEP,78}, {ENUM_PLAYSTYLE1_JOCKEY,70}},
    fka   = {{ENUM_PLAYSTYLE1_DEAD_BALL,68}},
    defaw = {{ENUM_PLAYSTYLE1_JOCKEY,70}},
    stntk = {{ENUM_PLAYSTYLE1_BLOCK,70}, {ENUM_PLAYSTYLE1_ENFORCER,76}},
    slitp = {{ENUM_PLAYSTYLE1_SLIDE_TACKLE,70}},
    -- Fix 2.2 : Promotion des Reactions
    rea   = {{ENUM_PLAYSTYLE1_INTERCEPT,70}, {ENUM_PLAYSTYLE1_ANTICIPATE,70}, {ENUM_PLAYSTYLE1_BLOCK,70}, {ENUM_PLAYSTYLE1_FIRST_TOUCH,70}, {ENUM_PLAYSTYLE1_TIKI_TAKA,75}, {ENUM_PLAYSTYLE1_JOCKEY,70}, {ENUM_PLAYSTYLE1_TECHNICAL,75}, {ENUM_PLAYSTYLE1_RAPID,76}, {ENUM_PLAYSTYLE1_QUICK_STEP,78}, {ENUM_PLAYSTYLE1_TRICKSTER,72}, {ENUM_PLAYSTYLE1_AERIAL_FORTRESS,70}, {ENUM_PLAYSTYLE1_INCISIVE_PASS,72}, {ENUM_PLAYSTYLE1_INVENTIVE,74}, {ENUM_PLAYSTYLE1_ACROBATIC,75}, {ENUM_PLAYSTYLE1_ENFORCER,76}},
    -- Fix 2.1 : Proxies manquants
    vis   = {{ENUM_PLAYSTYLE1_TIKI_TAKA,73}, {ENUM_PLAYSTYLE1_INCISIVE_PASS,72}, {ENUM_PLAYSTYLE1_INVENTIVE,74}, {ENUM_PLAYSTYLE1_PINGED_PASS,72}, {ENUM_PLAYSTYLE1_LONG_BALL_PASS,70}},
    bcon  = {{ENUM_PLAYSTYLE1_TRICKSTER,72}, {ENUM_PLAYSTYLE1_TECHNICAL,75}, {ENUM_PLAYSTYLE1_FIRST_TOUCH,70}, {ENUM_PLAYSTYLE1_TIKI_TAKA,73}, {ENUM_PLAYSTYLE1_GAMECHANGER,65}},
    bal   = {{ENUM_PLAYSTYLE1_TRICKSTER,72}, {ENUM_PLAYSTYLE1_JOCKEY,70}},
    agg   = {{ENUM_PLAYSTYLE1_PRESS_PROVEN,72}, {ENUM_PLAYSTYLE1_RELENTLESS,76}, {ENUM_PLAYSTYLE1_ENFORCER,76}},
    comp  = {{ENUM_PLAYSTYLE1_GAMECHANGER,65}, {ENUM_PLAYSTYLE1_PRESS_PROVEN,72}, {ENUM_PLAYSTYLE1_TIKI_TAKA,73}},
}

-- ============================================================
-- DICTIONNAIRES : PLAYSTYLES ET POSTES
-- ============================================================
local ALL_PS_ENUMS = {
    ENUM_PLAYSTYLE1_FINESSE_SHOT, ENUM_PLAYSTYLE1_CHIP_SHOT, ENUM_PLAYSTYLE1_POWER_SHOT,
    ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT, ENUM_PLAYSTYLE1_ACROBATIC, ENUM_PLAYSTYLE1_GAMECHANGER,
    ENUM_PLAYSTYLE1_DEAD_BALL, ENUM_PLAYSTYLE1_TIKI_TAKA, ENUM_PLAYSTYLE1_INCISIVE_PASS,
    ENUM_PLAYSTYLE1_PINGED_PASS, ENUM_PLAYSTYLE1_LONG_BALL_PASS, ENUM_PLAYSTYLE1_WHIPPED_PASS,
    ENUM_PLAYSTYLE1_INVENTIVE, ENUM_PLAYSTYLE1_TRICKSTER, ENUM_PLAYSTYLE1_TECHNICAL,
    ENUM_PLAYSTYLE1_PRESS_PROVEN, ENUM_PLAYSTYLE1_RAPID, ENUM_PLAYSTYLE1_QUICK_STEP,
    ENUM_PLAYSTYLE1_INTERCEPT, ENUM_PLAYSTYLE1_ANTICIPATE, ENUM_PLAYSTYLE1_JOCKEY,
    ENUM_PLAYSTYLE1_BLOCK, ENUM_PLAYSTYLE1_SLIDE_TACKLE, ENUM_PLAYSTYLE1_BRUISER,
    ENUM_PLAYSTYLE1_ENFORCER, ENUM_PLAYSTYLE1_LONG_THROW, ENUM_PLAYSTYLE1_RELENTLESS,
    ENUM_PLAYSTYLE1_FIRST_TOUCH, ENUM_PLAYSTYLE1_AERIAL_FORTRESS, ENUM_PLAYSTYLE1_PRECISION_HEADER
}

local GK_PS_ENUMS = {
    ENUM_PLAYSTYLE2_GK_CROSS_CLAIMER, ENUM_PLAYSTYLE2_GK_FAR_THROW, ENUM_PLAYSTYLE2_GK_RUSH_OUT,
    ENUM_PLAYSTYLE2_GK_FAR_REACH, ENUM_PLAYSTYLE2_GK_FOOTWORK, ENUM_PLAYSTYLE2_GK_DEFLECTOR
}

-- Prérequis GK (AXE 10b)
local GK_PREREQS = {
    [ENUM_PLAYSTYLE2_GK_DEFLECTOR]     = {stat1="gkref", stat2="gkdiv", hard=68, soft=78},
    [ENUM_PLAYSTYLE2_GK_FAR_REACH]     = {stat1="gkdiv", stat2="gkpos", hard=70, soft=80},
    [ENUM_PLAYSTYLE2_GK_CROSS_CLAIMER] = {stat1="gkhan", stat2="gkpos", hard=68, soft=78},
    [ENUM_PLAYSTYLE2_GK_RUSH_OUT]      = {stat1="gkpos", stat2="spd",   hard=65, soft=75},
    [ENUM_PLAYSTYLE2_GK_FOOTWORK]      = {stat1="gkkic", stat2="bcon",  hard=65, soft=75},
    [ENUM_PLAYSTYLE2_GK_FAR_THROW]     = {stat1="gkkic", stat2="str",   hard=62, soft=72},
}

local function get_position_category(pos)
    if pos == 0 then return "GK" end
    if pos == 12 or pos == 16 or pos == 23 or pos == 27 then return "WING" end
    if pos >= 2 and pos <= 8 then
        if pos == 4 or pos == 5 or pos == 6 then return "CB" else return "FB" end
    end
    if pos >= 9 and pos <= 15 then return "CM" end
    if pos >= 17 and pos <= 19 then return "CAM" end
    if pos >= 20 and pos <= 26 then return "ST" end
    return "UNKNOWN"
end

local POS_MENUS = {
    ["CB"] = {
        core = {ENUM_PLAYSTYLE1_BLOCK, ENUM_PLAYSTYLE1_INTERCEPT, ENUM_PLAYSTYLE1_ANTICIPATE, ENUM_PLAYSTYLE1_BRUISER, ENUM_PLAYSTYLE1_AERIAL_FORTRESS},
        flex = {ENUM_PLAYSTYLE1_JOCKEY, ENUM_PLAYSTYLE1_SLIDE_TACKLE, ENUM_PLAYSTYLE1_LONG_BALL_PASS, ENUM_PLAYSTYLE1_PRECISION_HEADER, ENUM_PLAYSTYLE1_ENFORCER}
    },
    ["FB"] = {
        core = {ENUM_PLAYSTYLE1_JOCKEY, ENUM_PLAYSTYLE1_ANTICIPATE, ENUM_PLAYSTYLE1_WHIPPED_PASS, ENUM_PLAYSTYLE1_RAPID, ENUM_PLAYSTYLE1_RELENTLESS},
        flex = {ENUM_PLAYSTYLE1_BLOCK, ENUM_PLAYSTYLE1_INTERCEPT, ENUM_PLAYSTYLE1_SLIDE_TACKLE, ENUM_PLAYSTYLE1_QUICK_STEP, ENUM_PLAYSTYLE1_FIRST_TOUCH, ENUM_PLAYSTYLE1_PINGED_PASS}
    },
    ["CM"] = {
        core = {ENUM_PLAYSTYLE1_TIKI_TAKA, ENUM_PLAYSTYLE1_INCISIVE_PASS, ENUM_PLAYSTYLE1_PINGED_PASS, ENUM_PLAYSTYLE1_LONG_BALL_PASS, ENUM_PLAYSTYLE1_WHIPPED_PASS, ENUM_PLAYSTYLE1_INVENTIVE, ENUM_PLAYSTYLE1_POWER_SHOT},
        flex = {ENUM_PLAYSTYLE1_INTERCEPT, ENUM_PLAYSTYLE1_ANTICIPATE, ENUM_PLAYSTYLE1_BRUISER, ENUM_PLAYSTYLE1_RELENTLESS, ENUM_PLAYSTYLE1_PRESS_PROVEN, ENUM_PLAYSTYLE1_FIRST_TOUCH, ENUM_PLAYSTYLE1_TECHNICAL, ENUM_PLAYSTYLE1_JOCKEY, ENUM_PLAYSTYLE1_BLOCK, ENUM_PLAYSTYLE1_AERIAL_FORTRESS, ENUM_PLAYSTYLE1_RAPID, ENUM_PLAYSTYLE1_QUICK_STEP, ENUM_PLAYSTYLE1_FINESSE_SHOT}
    },
    ["CAM"] = {
        core = {ENUM_PLAYSTYLE1_TIKI_TAKA, ENUM_PLAYSTYLE1_INCISIVE_PASS, ENUM_PLAYSTYLE1_TECHNICAL, ENUM_PLAYSTYLE1_FIRST_TOUCH, ENUM_PLAYSTYLE1_FINESSE_SHOT, ENUM_PLAYSTYLE1_INVENTIVE},
        flex = {ENUM_PLAYSTYLE1_RAPID, ENUM_PLAYSTYLE1_QUICK_STEP, ENUM_PLAYSTYLE1_TRICKSTER, ENUM_PLAYSTYLE1_PINGED_PASS, ENUM_PLAYSTYLE1_DEAD_BALL, ENUM_PLAYSTYLE1_RELENTLESS, ENUM_PLAYSTYLE1_CHIP_SHOT, ENUM_PLAYSTYLE1_POWER_SHOT}
    },
    ["WING"] = {
        core = {ENUM_PLAYSTYLE1_RAPID, ENUM_PLAYSTYLE1_QUICK_STEP, ENUM_PLAYSTYLE1_TECHNICAL, ENUM_PLAYSTYLE1_FINESSE_SHOT, ENUM_PLAYSTYLE1_FIRST_TOUCH, ENUM_PLAYSTYLE1_TRICKSTER},
        flex = {ENUM_PLAYSTYLE1_WHIPPED_PASS, ENUM_PLAYSTYLE1_INCISIVE_PASS, ENUM_PLAYSTYLE1_CHIP_SHOT, ENUM_PLAYSTYLE1_ACROBATIC, ENUM_PLAYSTYLE1_DEAD_BALL, ENUM_PLAYSTYLE1_RELENTLESS, ENUM_PLAYSTYLE1_POWER_SHOT, ENUM_PLAYSTYLE1_GAMECHANGER}
    },
    ["ST"] = {
        core = {ENUM_PLAYSTYLE1_FINESSE_SHOT, ENUM_PLAYSTYLE1_POWER_SHOT, ENUM_PLAYSTYLE1_PRECISION_HEADER, ENUM_PLAYSTYLE1_FIRST_TOUCH, ENUM_PLAYSTYLE1_CHIP_SHOT, ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT},
        flex = {ENUM_PLAYSTYLE1_RAPID, ENUM_PLAYSTYLE1_QUICK_STEP, ENUM_PLAYSTYLE1_AERIAL_FORTRESS, ENUM_PLAYSTYLE1_ACROBATIC, ENUM_PLAYSTYLE1_TECHNICAL, ENUM_PLAYSTYLE1_PRESS_PROVEN, ENUM_PLAYSTYLE1_RELENTLESS, ENUM_PLAYSTYLE1_GAMECHANGER}
    }
}

local function is_offrole(ps_id, cat)
    local menu = POS_MENUS[cat]
    if not menu then return false end
    return (not contains(menu.core, ps_id)) and (not contains(menu.flex, ps_id))
end

-- ============================================================
-- AXE 3 : MOTEUR DE PROFILS TACTIQUES (Moyenne Harmonique)
-- ============================================================
local function get_tactical_profile_bonus(cat, sc)
    local bonuses = {}
    local best_score = 0
    local function add_bonus(ps_id, base, factor_fn)
        table.insert(bonuses, {ps_id = ps_id, base = base, factor = factor_fn})
    end

    if cat == "CM" or cat == "CAM" then
        -- Moyenne harmonique : pénalise naturellement les lacunes
        local b2b = harmonic_mean(sc.sta, sc.shpow, sc.stntk, sc.attpos)
        local playmaker = harmonic_mean(sc.vis, sc.pas, sc.cur, sc.dri)
        local destroyer = harmonic_mean(sc.agg, sc.str, sc.icp, sc.stntk)

        best_score = math.max(b2b, playmaker, destroyer)
        if best_score > 70 then
            if b2b >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_POWER_SHOT, 65, function(s) return s.shpow / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_RELENTLESS, 55, function(s) return s.sta / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_INTERCEPT, 45, function(s) return s.icp / 100 end)
            end
            if playmaker >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_FINESSE_SHOT, 60, function(s) return s.fin / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_DEAD_BALL, 50, function(s) return s.fka / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_WHIPPED_PASS, 55, function(s) return s.crs / 100 end)
            end
            if destroyer >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_BRUISER, 60, function(s) return s.str / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_ANTICIPATE, 50, function(s) return s.defaw / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_ENFORCER, 55, function(s) return (s.str + s.agg) / 200 end)
            end
        end
    elseif cat == "ST" then
        local target_man = harmonic_mean(sc.str, sc.hea, math.min(sc.hgt, 195), sc.jmp)
        local poacher = harmonic_mean(sc.fin, sc.attpos, sc.spd)
        local false9 = harmonic_mean(sc.pas, sc.vis, sc.dri, sc.fin)

        best_score = math.max(target_man, poacher, false9)
        if best_score > 72 then
            if target_man >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_AERIAL_FORTRESS, 65, function(s) return s.hea / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_BRUISER, 55, function(s) return s.str / 100 end)
            end
            if poacher >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_FIRST_TOUCH, 55, function(s) return s.bcon / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_CHIP_SHOT, 60, function(s) return s.fin / 100 end)
            end
            if false9 >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_INCISIVE_PASS, 55, function(s) return s.pas / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_TIKI_TAKA, 50, function(s) return s.pas / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_PINGED_PASS, 45, function(s) return s.lpa / 100 end)
            end
        end
    elseif cat == "WING" then
        local inside_fwd = harmonic_mean(sc.fin, sc.cur, sc.acc)
        local classic_wing = harmonic_mean(sc.crs, sc.spd, sc.sta)

        best_score = math.max(inside_fwd, classic_wing)
        if best_score > 72 then
            if inside_fwd >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_FINESSE_SHOT, 55, function(s) return s.fin / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_POWER_SHOT, 60, function(s) return s.shpow / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_GAMECHANGER, 50, function(s) return s.fin / 100 end)
            end
            if classic_wing >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_WHIPPED_PASS, 50, function(s) return s.crs / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_RAPID, 55, function(s) return s.spd / 100 end)
            end
        end
    elseif cat == "CB" or cat == "FB" then
        local ball_playing = harmonic_mean(sc.lpa, sc.vis, sc.comp)
        local att_fullback = harmonic_mean(sc.crs, sc.spd, sc.sta)

        best_score = math.max(ball_playing, att_fullback)
        if best_score > 70 then
            if ball_playing >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_PINGED_PASS, 55, function(s) return s.lpa / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_LONG_BALL_PASS, 50, function(s) return s.lpa / 100 end)
            end
            if cat == "FB" and att_fullback >= best_score - 2 then
                add_bonus(ENUM_PLAYSTYLE1_WHIPPED_PASS, 45, function(s) return s.crs / 100 end)
                add_bonus(ENUM_PLAYSTYLE1_RAPID, 50, function(s) return s.spd / 100 end)
            end
        end
    end

    return bonuses
end

-- ============================================================
-- AXE 9 : BASE TECHNIQUE SOFTMAX
-- ============================================================
local function calc_technical_base_v14(ps, sc)
    if ps == ENUM_PLAYSTYLE1_FINESSE_SHOT then
        return softmax_weighted({sc.fin, sc.cur, sc.lngs})
    elseif ps == ENUM_PLAYSTYLE1_POWER_SHOT then
        return softmax_weighted({sc.shpow, sc.fin, sc.lngs, sc.str}) -- Fix 2.1 (+str)
    elseif ps == ENUM_PLAYSTYLE1_CHIP_SHOT then
        return softmax_weighted({sc.fin, sc.bcon, sc.comp})
    elseif ps == ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT then
        return softmax_weighted({sc.fin, sc.shpow})
    elseif ps == ENUM_PLAYSTYLE1_DEAD_BALL then
        return softmax_weighted({sc.fka, sc.cur, sc.shpow})
    elseif ps == ENUM_PLAYSTYLE1_GAMECHANGER then
        return softmax_weighted({sc.fin, sc.cur, sc.bcon, sc.comp}) -- Fix 2.1 (+comp)
    elseif ps == ENUM_PLAYSTYLE1_RAPID then
        return softmax_weighted({sc.spd, sc.spd, sc.acc, sc.rea}) -- Fix 2.1 (dri->acc), Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_QUICK_STEP then
        return softmax_weighted({sc.acc, sc.acc, sc.agi, sc.rea}) -- Fix 2.1 (dri->agi), Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_TRICKSTER then
        return softmax_weighted({sc.dri, sc.agi, sc.bal, sc.bcon, sc.rea}) -- Fix 2.1 (+bcon), Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_TECHNICAL then
        return softmax_weighted({sc.dri, sc.bcon, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_PRESS_PROVEN then
        return softmax_weighted({sc.dri, sc.comp, sc.str, sc.sta, sc.agg, sc.rea}) -- Fix 2.1 (+sta,agg), Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_INTERCEPT then
        return softmax_weighted({sc.icp, sc.rea})
    elseif ps == ENUM_PLAYSTYLE1_ANTICIPATE then
        return softmax_weighted({sc.defaw, sc.rea, sc.icp})
    elseif ps == ENUM_PLAYSTYLE1_JOCKEY then
        return softmax_weighted({sc.defaw, sc.agi, sc.bal, sc.rea}) -- Fix 2.1 (+bal), Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_BLOCK then
        return softmax_weighted({sc.stntk, sc.rea, sc.defaw})
    elseif ps == ENUM_PLAYSTYLE1_ENFORCER then
        return softmax_weighted({sc.str, sc.str, sc.agg, sc.stntk, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_BRUISER then
        return sc.str
    elseif ps == ENUM_PLAYSTYLE1_SLIDE_TACKLE then
        return sc.slitp
    elseif ps == ENUM_PLAYSTYLE1_AERIAL_FORTRESS then
        return softmax_weighted({sc.jmp, sc.str, sc.hea, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_PRECISION_HEADER then
        return softmax_weighted({sc.hea, sc.jmp, math.max(sc.fin, sc.str)})
    elseif ps == ENUM_PLAYSTYLE1_TIKI_TAKA then
        return softmax_weighted({sc.pas, sc.comp, sc.vis, sc.rea}) -- Fix 2.1 (attpos->vis), Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_INCISIVE_PASS then
        return softmax_weighted({sc.pas, sc.vis, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_WHIPPED_PASS then
        return softmax_weighted({sc.crs, sc.cur})
    elseif ps == ENUM_PLAYSTYLE1_PINGED_PASS then
        return softmax_weighted({sc.lpa, sc.vis, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_LONG_BALL_PASS then
        return softmax_weighted({sc.lpa, sc.vis, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_INVENTIVE then
        return softmax_weighted({sc.vis, sc.pas, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_FIRST_TOUCH then
        return softmax_weighted({sc.bcon, sc.rea})
    elseif ps == ENUM_PLAYSTYLE1_RELENTLESS then
        return softmax_weighted({sc.sta, sc.sta, sc.agg}) -- Fix 2.1 (softmax + agg)
    elseif ps == ENUM_PLAYSTYLE1_ACROBATIC then
        return softmax_weighted({sc.vol, sc.agi, sc.rea}) -- Fix 2.2 (+rea)
    elseif ps == ENUM_PLAYSTYLE1_LONG_THROW then
        return softmax_weighted({sc.str, sc.lpa})
    end
    return 0
end

-- ============================================================
-- MERIT SCORE V14.1 (Sprint 6)
-- Anchors the ranking in stat reality (technical base + raw peak)
-- rather than accumulated pool noise.
-- Returns: merit ∈ [0, 100]
-- ============================================================
local function calc_merit_v14(ps, sc, dna_pool, cat)
    local tech_base = 0
    if cat == "GK" then
        local tech_fn = GK_TECH_BASE[ps]
        tech_base = tech_fn and tech_fn(sc) or 0
    else
        tech_base = calc_technical_base_v14(ps, sc)
    end

    local entry = dna_pool[ps]
    local raw_base = entry and entry.base or 0

    return (CFG.PS_PLUS_WEIGHT_TECH * tech_base)
         + (CFG.PS_PLUS_WEIGHT_BASE * (raw_base / 100) * 100)
end

-- ============================================================
-- PS+ MERIT GATE (Logic for Elite PS+ qualification)
-- ============================================================
local function calc_ps_plus_merit(ps, sc, dna_pool, cat)
    -- Stat reality via generic merit
    local merit = calc_merit_v14(ps, sc, dna_pool, cat)

    -- Gate 1: technical quality must be elite
    local tech_base = (cat == "GK") and (GK_TECH_BASE[ps] and GK_TECH_BASE[ps](sc) or 0) 
                                   or calc_technical_base_v14(ps, sc)
    if tech_base < CFG.PS_PLUS_TECH_THRESHOLD then return -1 end

    -- Gate 2: underlying raw stat must also be genuinely strong
    local entry = dna_pool[ps]
    local raw_base = entry and entry.base or 0
    if raw_base < CFG.PS_PLUS_BASE_FLOOR then return -1 end

    return merit
end

-- ============================================================
-- AXE 7 : ACCUMULATION BORNÉE ADDITIVE (remplace norme L2)
-- new = cap · tanh(Σ / cap)  — rendements décroissants mais
-- récompense la compétence large contrairement à L2 qui
-- écrasait la discrimination (√(old²+delta²) ≈ 1.41d pour 2×d)
-- Sprint 1 fix : restores fairness across the score range
-- ============================================================
local function pool_add_bounded(pool, ps_id, score_delta, base_val)
    if not pool[ps_id] then pool[ps_id] = {score = 0, base = 0, raw_sum = 0} end
    local entry = pool[ps_id]
    local delta = math.max(0, score_delta)
    if delta > 0 then
        entry.raw_sum = (entry.raw_sum or 0) + delta
        entry.score = math.floor(CFG.POOL_CAP * math.tanh(entry.raw_sum / CFG.POOL_CAP))
    end
    entry.base = math.max(entry.base, base_val or 0)
end

-- Spécialistes contournent toujours le mécanisme borné (direct add)
local function pool_add_specialist(pool, ps_id, score_delta, base_val)
    if not pool[ps_id] then pool[ps_id] = {score = 0, base = 0} end
    pool[ps_id].score = pool[ps_id].score + math.max(0, score_delta)
    pool[ps_id].base = math.max(pool[ps_id].base, base_val or 0)
end

-- ============================================================
-- FILTRES DE POSITION (binaires — logiquement exclusifs)
-- ============================================================
local function is_ps_position_allowed(ps, cat)
    if cat == "CB" or cat == "FB" then
        if ps == ENUM_PLAYSTYLE1_FINESSE_SHOT or ps == ENUM_PLAYSTYLE1_CHIP_SHOT or ps == ENUM_PLAYSTYLE1_POWER_SHOT or ps == ENUM_PLAYSTYLE1_TRICKSTER then return false end
    end
    if cat == "ST" or cat == "WING" then
        if ps == ENUM_PLAYSTYLE1_BLOCK or ps == ENUM_PLAYSTYLE1_JOCKEY or ps == ENUM_PLAYSTYLE1_SLIDE_TACKLE or ps == ENUM_PLAYSTYLE1_ENFORCER or ps == ENUM_PLAYSTYLE1_ANTICIPATE then return false end
    end
    return true
end

-- ============================================================
-- PORTES STATISTIQUES SOUPLES (Sprint 1 fix)
-- Remplace les seuils binaires par des pénalités sigmoidales
-- continues via prereq_sigmoid. Retourne un multiplicateur [0,1].
-- ============================================================
local function calc_stat_gate_mu(ps, sc)
    local mu = 1.0

    if ps == ENUM_PLAYSTYLE1_AERIAL_FORTRESS then
        -- Original: hgt<185 AND jmp<85 → false
        -- Soft: OR-gate sur taille et détente (un des deux suffit)
        local mu_hgt = prereq_sigmoid(sc.hgt, 180, 190)
        local mu_jmp = prereq_sigmoid(sc.jmp, 80, 90)
        mu = mu * (1 - (1 - mu_hgt) * (1 - mu_jmp))  -- t-conorme probabiliste
    end

    if ps == ENUM_PLAYSTYLE1_PRECISION_HEADER then
        -- Original: hea<75 → false
        mu = mu * prereq_sigmoid(sc.hea, 70, 80)
    end

    if ps == ENUM_PLAYSTYLE1_ENFORCER then
        -- Original: str<80 → false
        mu = mu * prereq_sigmoid(sc.str, 75, 85)
    end

    if ps == ENUM_PLAYSTYLE1_TRICKSTER or ps == ENUM_PLAYSTYLE1_ACROBATIC then
        -- Original: agi<80 → false
        mu = mu * prereq_sigmoid(sc.agi, 75, 85)
    end

    if ps == ENUM_PLAYSTYLE1_RAPID or ps == ENUM_PLAYSTYLE1_QUICK_STEP then
        -- Original: max(spd,acc)<80 → false AND max(dri,bcon)<72 → false
        -- Soft: product of two gates (both must be present)
        mu = mu * prereq_sigmoid(math.max(sc.spd, sc.acc), 75, 85)
        mu = mu * prereq_sigmoid(math.max(sc.dri, sc.bcon), 67, 77)
    end

    return mu
end

-- Legacy wrapper for fallback code paths that still need boolean check
local function is_ps_hard_allowed(ps, sc, cat)
    if not is_ps_position_allowed(ps, cat) then return false end
    return calc_stat_gate_mu(ps, sc) > 0.10  -- ~equivalent to old hard cutoff region
end

-- ============================================================
-- CALCUL DU DNA POOL V14.1 (Intégration de tous les axes)
-- ============================================================
local function calc_dna_pool_v14(sc, cat, age, pref_foot, pos)
    local pool = {}
    local function add_normal(ps_id, score_delta, base_val)
        if not is_ps_position_allowed(ps_id, cat) then return end
        local gate_mu = calc_stat_gate_mu(ps_id, sc)
        local gated_delta = math.floor(score_delta * gate_mu)
        if gated_delta > 0 then
            pool_add_bounded(pool, ps_id, gated_delta, base_val)  -- AXE 7
        end
    end
    local function add_special(ps_id, score_delta, base_val)
        if not is_ps_position_allowed(ps_id, cat) then return end
        local gate_mu = calc_stat_gate_mu(ps_id, sc)
        local gated_delta = math.floor(score_delta * gate_mu)
        if gated_delta > 0 then
            pool_add_specialist(pool, ps_id, gated_delta, base_val)
        end
    end

    local ARCH_CORE_DELTA = 35
    local ARCH_FLEX_DELTA = 18

    -- ========================================================
    -- 1) Archetype scoring (Core/Flex + tactical profile)
    -- ========================================================
    local menu_base = POS_MENUS[cat] or {core = {}, flex = {}}
    local tactical_bonus = get_tactical_profile_bonus(cat, sc)

    local seen = {}
    for _, ps_id in ipairs(menu_base.core) do
        if not seen[ps_id] then
            add_normal(ps_id, ARCH_CORE_DELTA, 0)
            seen[ps_id] = true
        end
    end
    for _, ps_id in ipairs(menu_base.flex) do
        if not seen[ps_id] then
            add_normal(ps_id, ARCH_FLEX_DELTA, 0)
            seen[ps_id] = true
        end
    end
    for _, bonus in ipairs(tactical_bonus) do
        local ps_id = bonus.ps_id
        if not seen[ps_id] then
            local factor_val = bonus.factor(sc)
            local scored_delta = math.floor(bonus.base * math.max(0.5, factor_val))
            add_normal(ps_id, scored_delta, 0)
            seen[ps_id] = true
        end
    end

    -- ========================================================
    -- 2) Technical scanner (AXE 1 : sigmoïde)
    -- ========================================================
    for stat_key, val in pairs(sc) do
        local mappings = STAT_TO_PS_MAP[stat_key]
        if mappings and type(val) == "number" then
            for _, mapping in ipairs(mappings) do
                local ps_id = mapping[1]
                local threshold = mapping[2]
                local score_delta = stat_score_sigmoid(val, threshold)   -- AXE 1
                                  + age_bonus_gaussian(age, ps_id)      -- AXE 6
                                  + proportional_noise_v14(val, sc.comp or 50) -- AXE 8
                if score_delta > 0 then
                    add_normal(ps_id, score_delta, val)
                end
            end
        end
    end

    -- ========================================================
    -- 3) Bonus physiques & contextuels
    -- ========================================================
    local skills = math.max(1, math.min(5, math.floor(tonumber(sc.skills or sc.skillmoves) or 2)))
    local weakft = math.max(1, math.min(5, math.floor(tonumber(sc.weakft) or 2)))

    -- A. Bonus de taille
    if sc.hgt >= 185 then
        local hb = math.min(45, (sc.hgt - 185) * 3)
        add_normal(ENUM_PLAYSTYLE1_AERIAL_FORTRESS, hb, sc.hgt)
        add_normal(ENUM_PLAYSTYLE1_PRECISION_HEADER, math.floor(hb * 0.7), sc.hgt)
    end
    if sc.hgt >= 191 then
        add_normal(ENUM_PLAYSTYLE1_BRUISER, 18, sc.hgt)
    end

    -- B. Filtres durs par taille
    if sc.hgt < CFG.HEIGHT_MIN_AERIAL then pool[ENUM_PLAYSTYLE1_AERIAL_FORTRESS] = nil end
    if sc.hgt < CFG.HEIGHT_MIN_HEADER then pool[ENUM_PLAYSTYLE1_PRECISION_HEADER] = nil end

    -- C. Long Throw (multi-facteur)
    if sc.hgt >= 182 and sc.str >= 72 then
        local lt = math.min(55, (sc.hgt - 182) * 2.5 + (sc.str - 72) * 1.5)
        add_normal(ENUM_PLAYSTYLE1_LONG_THROW, lt, sc.str)
    end

    -- D. Enforcer (multi-facteur)
    if sc.str >= 78 and sc.stntk >= 76 then
        local enf = math.min(40, (sc.str - 78) * 3 + (sc.stntk - 76) * 2)
        add_normal(ENUM_PLAYSTYLE1_ENFORCER, enf, sc.str)
    end

    -- E. Skill moves
    if skills >= 3 then
        add_normal(ENUM_PLAYSTYLE1_TRICKSTER, (skills - 2) * 20, skills)
        add_normal(ENUM_PLAYSTYLE1_TECHNICAL, (skills - 2) * 15, skills)
        if skills == 5 then
            add_normal(ENUM_PLAYSTYLE1_QUICK_STEP, 15, skills)
            add_normal(ENUM_PLAYSTYLE1_ACROBATIC, 12, skills)
        end
    end

    -- F. Mauvais pied
    if weakft >= 3 and sc.comp >= 63 then
        add_normal(ENUM_PLAYSTYLE1_FINESSE_SHOT, (weakft - 2) * 15, weakft)
        add_normal(ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT, (weakft - 2) * 6, weakft)
    end

    -- G. AXE 10e : Bonus pied préféré pour inverted wingers
    -- pos 12/16 = ailes gauches, pos 23/27 = ailes droites
    -- pref_foot : 1 = droitier, 2 = gaucher (convention EA)
    if pref_foot and cat == "WING" then
        local is_inverted = false
        if (pos == 12 or pos == 16) and pref_foot == 1 then is_inverted = true end  -- ailier gauche droitier
        if (pos == 23 or pos == 27) and pref_foot == 2 then is_inverted = true end  -- ailier droit gaucher
        if is_inverted then
            -- Boost massif pour les tirs enroulés (cut inside)
            add_normal(ENUM_PLAYSTYLE1_FINESSE_SHOT, 40, sc.fin)
            add_normal(ENUM_PLAYSTYLE1_POWER_SHOT, 25, sc.shpow)
            add_normal(ENUM_PLAYSTYLE1_GAMECHANGER, 20, sc.fin)
        end
    end

    -- ========================================================
    -- 4) AXE 2 : Specialist tiers (exponentiel continu)
    -- ========================================================
    local SPECIALIST_MAP = {
        {stat = "spd", ps = ENUM_PLAYSTYLE1_RAPID},
        {stat = "acc", ps = ENUM_PLAYSTYLE1_QUICK_STEP},
        {stat = "dri", ps = ENUM_PLAYSTYLE1_TECHNICAL},
        {stat = "fin", ps = ENUM_PLAYSTYLE1_FINESSE_SHOT},
        {stat = "pas", ps = ENUM_PLAYSTYLE1_TIKI_TAKA},
        {stat = "icp", ps = ENUM_PLAYSTYLE1_INTERCEPT},
        {stat = "str", ps = ENUM_PLAYSTYLE1_BRUISER},
        {stat = "sta", ps = ENUM_PLAYSTYLE1_RELENTLESS},
        {stat = "hea", ps = ENUM_PLAYSTYLE1_AERIAL_FORTRESS},
        {stat = "fka", ps = ENUM_PLAYSTYLE1_DEAD_BALL},
    }

    for _, spec in ipairs(SPECIALIST_MAP) do
        local val = sc[spec.stat] or 0
        local bonus = specialist_bonus(val)  -- AXE 2 : exponentiel continu
        if bonus > 0 then
            add_special(spec.ps, bonus, val)
        end
    end

    -- ========================================================
    -- 5) AXE 5 : Synergy system (transfert logarithmique)
    -- Sprint 3 fix : Order-independent, capped at one transfer per PS
    -- ========================================================
    local SYNERGIES = {
        {ENUM_PLAYSTYLE1_TIKI_TAKA,       ENUM_PLAYSTYLE1_FIRST_TOUCH},
        {ENUM_PLAYSTYLE1_INCISIVE_PASS,   ENUM_PLAYSTYLE1_PINGED_PASS},
        {ENUM_PLAYSTYLE1_WHIPPED_PASS,    ENUM_PLAYSTYLE1_LONG_BALL_PASS},
        {ENUM_PLAYSTYLE1_INVENTIVE,       ENUM_PLAYSTYLE1_TIKI_TAKA},
        {ENUM_PLAYSTYLE1_TRICKSTER,       ENUM_PLAYSTYLE1_FIRST_TOUCH},
        {ENUM_PLAYSTYLE1_TECHNICAL,       ENUM_PLAYSTYLE1_TRICKSTER},
        {ENUM_PLAYSTYLE1_ACROBATIC,       ENUM_PLAYSTYLE1_TECHNICAL},
        {ENUM_PLAYSTYLE1_LOW_DRIVEN_SHOT, ENUM_PLAYSTYLE1_FINESSE_SHOT},
        {ENUM_PLAYSTYLE1_INTERCEPT,       ENUM_PLAYSTYLE1_ANTICIPATE},
        {ENUM_PLAYSTYLE1_PRESS_PROVEN,    ENUM_PLAYSTYLE1_INTERCEPT},
        {ENUM_PLAYSTYLE1_SLIDE_TACKLE,    ENUM_PLAYSTYLE1_BLOCK},
        {ENUM_PLAYSTYLE1_BRUISER,         ENUM_PLAYSTYLE1_AERIAL_FORTRESS},
        {ENUM_PLAYSTYLE1_AERIAL_FORTRESS, ENUM_PLAYSTYLE1_PRECISION_HEADER},
        {ENUM_PLAYSTYLE1_RELENTLESS,      ENUM_PLAYSTYLE1_PRESS_PROVEN},
        {ENUM_PLAYSTYLE1_ENFORCER,        ENUM_PLAYSTYLE1_BRUISER},
        {ENUM_PLAYSTYLE1_LONG_THROW,      ENUM_PLAYSTYLE1_AERIAL_FORTRESS},
        {ENUM_PLAYSTYLE1_LONG_BALL_PASS,  ENUM_PLAYSTYLE1_LONG_THROW},
        {ENUM_PLAYSTYLE1_DEAD_BALL,       ENUM_PLAYSTYLE1_FINESSE_SHOT},
        -- Fix 3.2 : New pairs
        {ENUM_PLAYSTYLE1_RAPID,           ENUM_PLAYSTYLE1_QUICK_STEP},
        {ENUM_PLAYSTYLE1_QUICK_STEP,      ENUM_PLAYSTYLE1_RAPID},
        {ENUM_PLAYSTYLE1_INCISIVE_PASS,   ENUM_PLAYSTYLE1_INVENTIVE},
        {ENUM_PLAYSTYLE1_ANTICIPATE,      ENUM_PLAYSTYLE1_JOCKEY},
    }

    -- Snapshot scores to ensure order-independence (fix §4)
    local snapshots = {}
    for id, entry in pairs(pool) do snapshots[id] = entry.score end

    -- Collect best transfer for each target (fix §4.1)
    local best_transfers = {}
    for _, pair in ipairs(SYNERGIES) do
        local src_score = snapshots[pair[1]] or 0
        if src_score >= CFG.SYNERGY_THRESHOLD then
            local transfer = synergy_transfer(src_score)
            if transfer > 0 then
                best_transfers[pair[2]] = math.max(best_transfers[pair[2]] or 0, transfer)
            end
        end
    end

    -- Apply capped transfers
    for target_id, transfer in pairs(best_transfers) do
        add_normal(target_id, transfer, 0)
    end

    -- ========================================================
    -- 6) AXE 4 : Prérequis sigmoïdaux continus
    -- ========================================================
    apply_prereqs_filter_v14(pool, sc)

    return pool
end

-- ============================================================
-- GK TECH BASE (normalized stat composites for GK PS+)
-- calc_technical_base_v14 does not cover GK playstyles, so we define
-- equivalent per-PS stat composites using the same stats as calc_gk_pool_v14.
-- ============================================================
local GK_TECH_BASE = {
    [ENUM_PLAYSTYLE2_GK_DEFLECTOR]     = function(s) return (s.gkref + s.gkdiv) / 2 end,
    [ENUM_PLAYSTYLE2_GK_FAR_REACH]     = function(s) return (s.gkdiv + s.gkref + s.gkpos) / 3 end,
    [ENUM_PLAYSTYLE2_GK_CROSS_CLAIMER] = function(s) return (s.gkhan + s.gkpos) / 2 end,
    [ENUM_PLAYSTYLE2_GK_RUSH_OUT]      = function(s) return (s.gkpos + s.acc + s.spd) / 3 end,
    [ENUM_PLAYSTYLE2_GK_FOOTWORK]      = function(s) return (s.gkkic + s.rea + s.bcon) / 3 end,
    [ENUM_PLAYSTYLE2_GK_FAR_THROW]     = function(s) return (s.gkkic + s.lpa + s.str) / 3 end,
}

-- ============================================================
-- GK POOL V14.1 (avec prérequis - AXE 10b)
-- ============================================================
local function calc_gk_pool_v14(sc)
    local pool = {}
    local function gk_add(ps_id, score_delta, base_val)
        pool_add_bounded(pool, ps_id, score_delta, base_val)  -- AXE 7
    end

    -- Shot stopper archetype
    gk_add(ENUM_PLAYSTYLE2_GK_DEFLECTOR, stat_score_sigmoid((sc.gkref + sc.gkdiv) / 2, 74), (sc.gkref + sc.gkdiv) / 2)
    gk_add(ENUM_PLAYSTYLE2_GK_FAR_REACH, stat_score_sigmoid((sc.gkdiv + sc.gkref + sc.gkpos) / 3, 75), (sc.gkdiv + sc.gkref + sc.gkpos) / 3)
    gk_add(ENUM_PLAYSTYLE2_GK_CROSS_CLAIMER, stat_score_sigmoid((sc.gkhan + sc.gkpos) / 2, 73), (sc.gkhan + sc.gkpos) / 2)

    -- Sweeper keeper archetype
    gk_add(ENUM_PLAYSTYLE2_GK_RUSH_OUT, stat_score_sigmoid((sc.gkpos + sc.acc + sc.spd) / 3, 72), (sc.gkpos + sc.acc + sc.spd) / 3)
    gk_add(ENUM_PLAYSTYLE2_GK_FOOTWORK, stat_score_sigmoid((sc.gkkic + sc.rea + sc.bcon) / 3, 72), (sc.gkkic + sc.rea + sc.bcon) / 3)
    gk_add(ENUM_PLAYSTYLE2_GK_FAR_THROW, stat_score_sigmoid((sc.gkkic + sc.lpa + sc.str) / 3, 70), (sc.gkkic + sc.lpa + sc.str) / 3)

    -- Height context bonuses
    if sc.hgt >= 190 then
        gk_add(ENUM_PLAYSTYLE2_GK_FAR_REACH, 28, sc.hgt)
        gk_add(ENUM_PLAYSTYLE2_GK_CROSS_CLAIMER, 22, sc.hgt)
    elseif sc.hgt <= 184 then
        gk_add(ENUM_PLAYSTYLE2_GK_RUSH_OUT, 16, sc.hgt)
        gk_add(ENUM_PLAYSTYLE2_GK_FOOTWORK, 12, sc.hgt)
    end

    -- AXE 10b : Appliquer prérequis GK (sigmoïdaux)
    for ps_id, entry in pairs(pool) do
        local prereq = GK_PREREQS[ps_id]
        if prereq and entry and entry.score > 0 then
            local v1 = sc[prereq.stat1] or 0
            local v2 = sc[prereq.stat2] or 0
            local avg = (v1 + v2) / 2
            local mu = prereq_sigmoid(avg, prereq.hard, prereq.soft)
            entry.score = math.floor(entry.score * mu)
        end
    end

    return pool
end

-- ============================================================
-- OUTILS DE SECURITE
-- ============================================================
local function safeGetField(tbl, rec, fieldname)
    local ok, val = pcall(function() return tbl:GetRecordFieldValue(rec, fieldname) end)
    if ok then return val end
    return nil
end

local function safeSetField(tbl, rec, fieldname, value)
    pcall(function() tbl:SetRecordFieldValue(rec, fieldname, value) end)
end

local function extract_age_from_birthdate(birthdate_val)
    local raw = tonumber(birthdate_val)
    if not raw then return nil end

    local year = nil
    if raw > 10000000 then
        year = math.floor(raw / 10000)
    elseif raw > 1000 and raw < 3000 then
        year = raw
    end
    if not year then return nil end

    local now_year = os.date("*t").year
    local age = now_year - year
    if age < 14 or age > 60 then return nil end
    return age
end

-- AXE 10a : Hash déterministe (Knuth multiplicatif)
-- Sprint 1 fix : suppression du XOR os.time() qui détruisait la reproductibilité
local function deterministic_seed(pid)
    local knuth = 2654435761
    local hash = (pid * knuth) % (2 ^ 31)
    return hash
end

-- ============================================================
-- AXE 10c : Seuil organique dynamique
-- threshold = base - (pool_size - ref) * adjust
-- ============================================================
local function dynamic_organic_threshold(dynamic_pool_size)
    local raw = CFG.ORGANIC_BASE_THRESHOLD - (dynamic_pool_size - CFG.ORGANIC_POOL_REF) * CFG.ORGANIC_POOL_ADJUST
    return math.max(50, raw) -- AXE 10c : Floor à 50 (Sprint 5)
end

-- ============================================================
-- AXE 10f : SYSTEME D'EXCLUSIONS (Sprint 3 fix)
-- Prévient les combinaisons contradictoires (ex: Bruiser + Trickster)
-- ============================================================
local EXCLUSION_SETS = {
    {ps1 = ENUM_PLAYSTYLE1_BRUISER, ps2 = ENUM_PLAYSTYLE1_TRICKSTER},
    {ps1 = ENUM_PLAYSTYLE1_JOCKEY,  ps2 = ENUM_PLAYSTYLE1_RAPID, cond = function(cat) return cat == "CB" end},
}

local function apply_ps_exclusions(ps_list, cat, get_dna_fn)
    local to_remove = {}
    for _, set in ipairs(EXCLUSION_SETS) do
        if not set.cond or set.cond(cat) then
            local idx1, idx2
            for i, ps in ipairs(ps_list) do
                if ps == set.ps1 then idx1 = i
                elseif ps == set.ps2 then idx2 = i end
            end

            if idx1 and idx2 then
                -- Garder celui qui a le meilleur score DNA
                local s1 = get_dna_fn(set.ps1)
                local s2 = get_dna_fn(set.ps2)
                if s1 >= s2 then table.insert(to_remove, idx2)
                else table.insert(to_remove, idx1) end
            end
        end
    end

    if #to_remove > 0 then
        table.sort(to_remove, function(a, b) return a > b end) -- supprimer par la fin
        for _, idx in ipairs(to_remove) do
            table.remove(ps_list, idx)
        end
    end
end

-- ============================================================
-- PROCESSUS PRINCIPAL V14.1
-- ============================================================
local function run_team_setup()
    local players_table = LE.db:GetTable("players")

    if not players_table then return end

    local total_players = 0
    local log_lines = {}

    -- Get player IDs directly from the managed team (set: pid -> true)
    local team_pids = GetUserSeniorTeamPlayerIDs(tostring(USER_TEAM_ID))
    if not team_pids then return end

    local players_map = {}
    local p_rec = players_table:GetFirstRecord()
    while p_rec > 0 do
        local pid = safeGetField(players_table, p_rec, "playerid") or safeGetField(players_table, p_rec, "artificialkey")
        if pid and team_pids[pid] then players_map[pid] = p_rec end
        p_rec = players_table:GetNextValidRecord()
    end

    for pid, record in pairs(players_map) do
        total_players = total_players + 1

        local ovr  = tonumber(safeGetField(players_table, record, "overallrating") or 50)
        local pot  = tonumber(safeGetField(players_table, record, "potential") or 50)
        local pos  = tonumber(safeGetField(players_table, record, "preferredposition1") or 0)
        local name = GetPlayerName(pid) or "Inconnu"
        local cat  = get_position_category(pos)
        local age  = extract_age_from_birthdate(safeGetField(players_table, record, "birthdate"))

        -- AXE 10a : Seed déterministe
        math.randomseed(deterministic_seed(pid))

        -- AXE 10e : Pied préféré
        local pref_foot = tonumber(safeGetField(players_table, record, "preferredfoot") or 0)

        local sc = {
            hgt   = tonumber(safeGetField(players_table, record, "height") or 175),
            dri   = tonumber(safeGetField(players_table, record, "dribbling") or 50),
            spd   = tonumber(safeGetField(players_table, record, "sprintspeed") or 50),
            acc   = tonumber(safeGetField(players_table, record, "acceleration") or 50),
            fin   = tonumber(safeGetField(players_table, record, "finishing") or 50),
            pas   = tonumber(safeGetField(players_table, record, "shortpassing") or 50),
            vis   = tonumber(safeGetField(players_table, record, "vision") or 50),
            sta   = tonumber(safeGetField(players_table, record, "stamina") or 50),
            str   = tonumber(safeGetField(players_table, record, "strength") or 50),
            icp   = tonumber(safeGetField(players_table, record, "interceptions") or 50),
            defaw = tonumber(safeGetField(players_table, record, "defensiveawareness") or 50),
            stntk = tonumber(safeGetField(players_table, record, "standingtackle") or 50),
            slitp = tonumber(safeGetField(players_table, record, "slidingtackle") or 50),
            hea   = tonumber(safeGetField(players_table, record, "headingaccuracy") or 50),
            agi   = tonumber(safeGetField(players_table, record, "agility") or 50),
            cur   = tonumber(safeGetField(players_table, record, "curve") or 50),
            shpow = tonumber(safeGetField(players_table, record, "shotpower") or 50),
            rea   = tonumber(safeGetField(players_table, record, "reactions") or 50),
            lpa   = tonumber(safeGetField(players_table, record, "longpassing") or 50),
            crs   = tonumber(safeGetField(players_table, record, "crossing") or 50),
            fka   = tonumber(safeGetField(players_table, record, "freekickaccuracy") or 50),
            jmp   = tonumber(safeGetField(players_table, record, "jumping") or 50),
            bcon  = tonumber(safeGetField(players_table, record, "ballcontrol") or 50),
            comp  = tonumber(safeGetField(players_table, record, "composure") or 50),
            agg   = tonumber(safeGetField(players_table, record, "aggression") or 50),
            vol   = tonumber(safeGetField(players_table, record, "volleys") or 50),
            attpos= tonumber(safeGetField(players_table, record, "positioning") or 50),
            lngs  = tonumber(safeGetField(players_table, record, "longshots") or 50),
            bal   = tonumber(safeGetField(players_table, record, "balance") or 50),
            skills    = tonumber(safeGetField(players_table, record, "skillmoves") or 2),
            skillmoves= tonumber(safeGetField(players_table, record, "skillmoves") or 2),
            weakft    = tonumber(safeGetField(players_table, record, "weakfootabilitytypecode") or 2),
            age       = age,

            -- GK stats
            gkdiv = tonumber(safeGetField(players_table, record, "gkdiving") or 0),
            gkref = tonumber(safeGetField(players_table, record, "gkreflexes") or 0),
            gkhan = tonumber(safeGetField(players_table, record, "gkhandling") or 0),
            gkpos = tonumber(safeGetField(players_table, record, "gkpositioning") or 0),
            gkkic = tonumber(safeGetField(players_table, record, "gkkicking") or 0)
        }

        -- Cache DNA
        local dna_pool = nil
        local function get_dna(ps)
            if not dna_pool then
                dna_pool = calc_dna_pool_v14(sc, cat, age, pref_foot, pos)  -- V14.1
            end
            local entry = dna_pool[ps]
            return entry and entry.score or 0
        end

        -- ========================================================
        -- 1. QUOTAS ORGANIQUES
        -- ========================================================
        local absolute_max_ps, max_gold = get_limits(ovr, pot)
        local guaranteed_min_ps = math.max(1, math.floor(absolute_max_ps * 0.5))

        -- ========================================================
        -- 2. GESTION ISOLEE DES GARDIENS
        -- ========================================================
        if cat == "GK" then
            local gk_pool = calc_gk_pool_v14(sc)  -- V14.1 avec prérequis
            local gk_candidates = {}
            for _, ps in ipairs(GK_PS_ENUMS) do
                local entry = gk_pool[ps]
                local score = entry and entry.score or 0
                if score > 0 then
                    table.insert(gk_candidates, {id = ps, score = score})
                end
            end
            table.sort(gk_candidates, function(a, b) return a.score > b.score end)

            local final_gk_list = {}
            for _, cand in ipairs(gk_candidates) do
                if #final_gk_list >= guaranteed_min_ps then break end
                table.insert(final_gk_list, cand.id)
            end
            for _, cand in ipairs(gk_candidates) do
                if #final_gk_list >= absolute_max_ps then break end
                if cand.score >= ORGANIC_UNLOCK_THRESHOLD and not contains(final_gk_list, cand.id) then
                    table.insert(final_gk_list, cand.id)
                end
            end
            if #final_gk_list == 0 then
                table.insert(final_gk_list, ENUM_PLAYSTYLE2_GK_RUSH_OUT)
            end

            local final_t2 = 0
            local final_i2 = 0
            for _, ps in ipairs(final_gk_list) do
                final_t2 = final_t2 | ps
            end
            -- GK PS+ gate (Improved — merit-based, same logic as outfield)
            local gk_plus_candidates = {}
            for _, ps in ipairs(final_gk_list) do
                local tech_fn = GK_TECH_BASE[ps]
                local tech_base = tech_fn and tech_fn(sc) or 0
                local entry = gk_pool[ps]
                local raw_base = entry and entry.base or 0
                if tech_base >= CFG.PS_PLUS_TECH_THRESHOLD and raw_base >= CFG.PS_PLUS_BASE_FLOOR then
                    local merit = (CFG.PS_PLUS_WEIGHT_TECH * tech_base)
                                + (CFG.PS_PLUS_WEIGHT_BASE * (raw_base / 100) * 100)
                    table.insert(gk_plus_candidates, {id = ps, merit = merit})
                end
            end
            table.sort(gk_plus_candidates, function(a, b) return a.merit > b.merit end)
            for i = 1, math.min(max_gold, #gk_plus_candidates) do
                final_i2 = final_i2 | gk_plus_candidates[i].id
            end

            if not USER_CONFIG.DRY_RUN then
                safeSetField(players_table, record, "trait2", final_t2)
                safeSetField(players_table, record, "icontrait2", final_i2)
            end
            table.insert(log_lines, string.format("%s (GK) | Traite", name))
        else
            -- ========================================================
            -- 3. MENU DYNAMIQUE (Core + Flex + Profil)
            -- ========================================================
            local menu_base = POS_MENUS[cat] or {core = {}, flex = {}}
            local tactical_bonus = get_tactical_profile_bonus(cat, sc)
            local function is_shooting_ps(ps_id)
                for _, sps in ipairs(SHOOTING_PS) do
                    if sps == ps_id then return true end
                end
                return false
            end
            local function boosted_sort_score(ps_id, score)
                local boosted = score or 0
                if contains(menu_base.core, ps_id) or contains(menu_base.flex, ps_id) then
                    boosted = boosted + ROLE_BOOST
                end
                if SHOOTING_POSITIONS[cat] and is_shooting_ps(ps_id) then
                    boosted = boosted + SHOOTING_BOOST
                end
                return boosted
            end

            local dynamic_pool = {}
            for _, ps in ipairs(menu_base.core) do table.insert(dynamic_pool, ps) end
            for _, ps in ipairs(menu_base.flex) do table.insert(dynamic_pool, ps) end
            for _, bonus in ipairs(tactical_bonus) do
                local ps = bonus.ps_id
                if not contains(dynamic_pool, ps) then table.insert(dynamic_pool, ps) end
            end

            -- AXE 10c : Seuil organique dynamique
            local organic_threshold = dynamic_organic_threshold(#dynamic_pool)

            -- ========================================================
            -- 4. AXE 12 : AUDIT DES ACQUIS AVEC DRIFT DE POSITION
            -- ========================================================
            local trait_field = "trait1"
            local icon_field  = "icontrait1"
            local current_trait_val = tonumber(safeGetField(players_table, record, trait_field) or 0)

            local valid_existing_traits = {}
            for _, ps in ipairs(ALL_PS_ENUMS) do
                if (current_trait_val & ps) ~= 0 then
                    local score = get_dna(ps)
                    if score >= AUDIT_KEEP_THRESHOLD then
                        -- AXE 12 : Appliquer decay selon la position dans le menu
                        local audit_score = score
                        if contains(menu_base.core, ps) then
                            -- Core du poste actuel : pas de decay
                            audit_score = score
                        elseif contains(menu_base.flex, ps) then
                            -- Flex du poste actuel : léger decay
                            audit_score = math.floor(score * CFG.AUDIT_FLEX_DECAY)
                        elseif is_offrole(ps, cat) then
                            -- Off-role (drift de position) : fort decay
                            audit_score = math.floor(score * CFG.AUDIT_OFFROLE_DECAY)
                        end

                        if audit_score >= AUDIT_KEEP_THRESHOLD then
                            table.insert(valid_existing_traits, {id = ps, score = audit_score})
                        end
                    end
                end
            end
            table.sort(valid_existing_traits, function(a, b) return a.score > b.score end)
            if #valid_existing_traits > CFG.AUDIT_MAX_RETAINED then
                local retained = {}
                for i = 1, CFG.AUDIT_MAX_RETAINED do
                    table.insert(retained, valid_existing_traits[i])
                end
                valid_existing_traits = retained
            end

            -- ========================================================
            -- 5. REMPLISSAGE ORGANIQUE
            -- ========================================================
            local final_ps_list = {}
            for _, entry in ipairs(valid_existing_traits) do
                table.insert(final_ps_list, entry.id)
            end

            local candidates = {}
            for _, ps in ipairs(ALL_PS_ENUMS) do
                if not contains(final_ps_list, ps) then
                    local score = get_dna(ps)
                    if score > 0 then
                        local merit = calc_merit_v14(ps, sc, dna_pool, cat)
                        if is_offrole(ps, cat) then
                            merit = merit * CFG.OFFROLE_PENALTY
                        end
                        table.insert(candidates, {id = ps, score = score, merit = merit})
                    end
                end
            end
            table.sort(candidates, function(a, b)
                local a_boosted = boosted_sort_score(a.id, a.merit)
                local b_boosted = boosted_sort_score(b.id, b.merit)
                if math.abs(a_boosted - b_boosted) < 0.001 then
                    return a.score > b.score -- AXE 10f : Pool score as primary tiebreaker only (Sprint 6)
                end
                return a_boosted > b_boosted
            end)

            -- AXE 10d : Compteur off-role incrémental (O(n) au lieu de O(n²))
            local offrole_count = 0
            for _, ps in ipairs(final_ps_list) do
                if is_offrole(ps, cat) then offrole_count = offrole_count + 1 end
            end

            for _, cand in ipairs(candidates) do
                if #final_ps_list >= guaranteed_min_ps then break end
                if is_offrole(cand.id, cat) then
                    if offrole_count < CFG.OFFROLE_MAX then
                        table.insert(final_ps_list, cand.id)
                        offrole_count = offrole_count + 1
                    end
                else
                    table.insert(final_ps_list, cand.id)
                end
            end

            for _, cand in ipairs(candidates) do
                if #final_ps_list >= absolute_max_ps then break end
                if cand.score >= organic_threshold and not contains(final_ps_list, cand.id) then
                    if is_offrole(cand.id, cat) then
                        if offrole_count < CFG.OFFROLE_MAX then
                            table.insert(final_ps_list, cand.id)
                            offrole_count = offrole_count + 1
                        end
                    else
                        table.insert(final_ps_list, cand.id)
                    end
                end
            end

            -- ========================================================
            -- AXE 11 : SHOOTING GUARANTEE OPTIMALE (ratio coût/bénéfice)
            -- ========================================================
            if SHOOTING_POSITIONS[cat] then
                local function count_shooting_ps()
                    local count = 0
                    for _, ps in ipairs(final_ps_list) do
                        if is_shooting_ps(ps) then count = count + 1 end
                    end
                    return count
                end

                while count_shooting_ps() < CFG.SHOOTING_MIN do
                    -- Trouver le meilleur shooting PS candidat
                    local best_shooting_cand = nil
                    local best_shooting_score = -1
                    for _, sps in ipairs(SHOOTING_PS) do
                        if not contains(final_ps_list, sps) then
                            local s = get_dna(sps)
                            if s > best_shooting_score then
                                best_shooting_score = s
                                best_shooting_cand = sps
                            end
                        end
                    end
                    if not best_shooting_cand or best_shooting_score <= 0 then break end

                    if #final_ps_list < absolute_max_ps then
                        table.insert(final_ps_list, best_shooting_cand)
                    else
                        -- AXE 11 : Trouver le remplacement optimal par ratio
                        local best_ratio = -1
                        local best_replace_idx = nil
                        for i, ps in ipairs(final_ps_list) do
                            if not is_shooting_ps(ps) then
                                local loss = math.max(1, get_dna(ps))
                                local ratio = best_shooting_score / loss
                                if ratio > best_ratio then
                                    best_ratio = ratio
                                    best_replace_idx = i
                                end
                            end
                        end
                        if not best_replace_idx then break end

                        -- Ne remplacer que si le ratio est raisonnable
                        if best_ratio >= 0.3 then
                            final_ps_list[best_replace_idx] = best_shooting_cand
                        else
                            break  -- ratio trop mauvais, on arrête
                        end
                    end
                end
            end

            -- AXE 10f : Appliquer exclusions (Sprint 3 fix)
            apply_ps_exclusions(final_ps_list, cat, get_dna)

            -- Troncature sécurité avec cache
            if #final_ps_list > absolute_max_ps then
                table.sort(final_ps_list, function(a, b)
                    local a_score = get_dna(a)
                    local b_score = get_dna(b)
                    local a_merit = calc_merit_v14(a, sc, dna_pool, cat)
                    local b_merit = calc_merit_v14(b, sc, dna_pool, cat)
                    local a_boosted = boosted_sort_score(a, a_merit)
                    local b_boosted = boosted_sort_score(b, b_merit)
                    if math.abs(a_boosted - b_boosted) < 0.001 then
                        return a_score > b_score
                    end
                    return a_boosted > b_boosted
                end)
                local truncated = {}
                for i = 1, absolute_max_ps do table.insert(truncated, final_ps_list[i]) end
                final_ps_list = truncated
            end

            -- AXE 10f : Fallback intelligent (tri par base technique au lieu d'arbitraire)
            if #final_ps_list == 0 then
                local fallback_candidates = {}
                local core_menu = (POS_MENUS[cat] and POS_MENUS[cat].core) or {}
                for _, ps in ipairs(core_menu) do
                    if is_ps_hard_allowed(ps, sc, cat) then
                        local tech_base = calc_technical_base_v14(ps, sc)
                        table.insert(fallback_candidates, {id = ps, score = tech_base})
                    end
                end
                table.sort(fallback_candidates, function(a, b) return a.score > b.score end)

                if #fallback_candidates > 0 then
                    table.insert(final_ps_list, fallback_candidates[1].id)
                else
                    -- Dernier recours absolu
                    table.insert(final_ps_list, ENUM_PLAYSTYLE1_FIRST_TOUCH)
                end
            end

            -- ========================================================
            -- 6. ELITE GATEKEEPER (Improved — merit-based PS+ selection)
            -- ========================================================
            local final_icon_list = {}
            if max_gold > 0 then
                -- Ensure dna_pool is computed (needed for entry.base access)
                if not dna_pool then
                    dna_pool = calc_dna_pool_v14(sc, cat, age, pref_foot, pos)
                end

                local ps_plus_candidates = {}
                for _, ps in ipairs(final_ps_list) do
                    local merit = calc_ps_plus_merit(ps, sc, dna_pool)
                    if merit >= 0 then  -- -1 means gated out
                        table.insert(ps_plus_candidates, {id = ps, merit = merit})
                    end
                end

                -- Sort by composite merit (technical base weighted 70%, raw base 30%)
                table.sort(ps_plus_candidates, function(a, b) return a.merit > b.merit end)

                for i = 1, math.min(max_gold, #ps_plus_candidates) do
                    table.insert(final_icon_list, ps_plus_candidates[i].id)
                end
            end

            -- ========================================================
            -- 7. VALIDATION HARNESS (AXE 10g - Sprint 7)
            -- Prints detailed metrics in DRY_RUN mode
            -- ========================================================
            if USER_CONFIG.DRY_RUN then
                print(string.format(">>> VALIDATION: %s (OVR:%d, CAT:%s)", name, ovr, cat))
                for i, ps in ipairs(final_ps_list) do
                    local is_plus = contains(final_icon_list, ps)
                    local entry = dna_pool[ps] or {}
                    local merit = calc_merit_v14(ps, sc, dna_pool, cat)
                    local tech = (cat == "GK" and GK_TECH_BASE[ps] and GK_TECH_BASE[ps](sc)) or calc_technical_base_v14(ps, sc)
                    
                    print(string.format("  [%d] %-20s | MERIT:%.1f | TECH:%.1f | POOL:%d | MU:%.2f %s",
                        i, tostring(ps), merit, tech, entry.score or 0, entry.prereq_mu or 1.0, is_plus and "[PS+]" or ""))
                end
                print("--------------------------------------------------------")
            end

            -- ========================================================
            -- 8. INJECTION BASE DE DONNEES
            -- ========================================================
            local final_trait_val = 0
            local final_icon_val = 0
            for _, ps in ipairs(final_ps_list) do final_trait_val = final_trait_val | ps end
            for _, ps in ipairs(final_icon_list) do final_icon_val = final_icon_val | ps end

            if not USER_CONFIG.DRY_RUN then
                safeSetField(players_table, record, trait_field, final_trait_val)
                safeSetField(players_table, record, icon_field, final_icon_val)
            end

            table.insert(log_lines, string.format("%s (OVR:%d) | PS: %d | PS+: %d",
                name, ovr, #final_ps_list, #final_icon_list))
        end
    end

    local summary = "--------------------------------------------------------\n"
    for i = 1, math.min(#log_lines, 12) do summary = summary .. log_lines[i] .. "\n" end
    if #log_lines > 12 then summary = summary .. string.format("... and %d more players.\n", #log_lines - 12) end
    summary = summary .. "--------------------------------------------------------"

    if USER_CONFIG.DRY_RUN then
        MessageBox("The PlayStyle Forge V3 (Engine V14.1) - DRY RUN MODE",
            string.format("[DRY RUN] Simulation complete: %d players analyzed for team %d.\n\nNO CHANGES have been applied to the database.\n\nBelow is what WOULD have been modified if DRY_RUN was set to false:\n\n%s",
            total_players, USER_TEAM_ID, summary))
    else
        MessageBox("The PlayStyle Forge V3 (Engine V14.1)",
            string.format("Update complete: %d players processed for team %d.\n\n%s\n\nIMPORTANT: Don't forget to SAVE your Career in-game to permanently keep these changes!",
            total_players, USER_TEAM_ID, summary))
    end
end

-- Execution
run_team_setup()
-- ================================ V3 - MASTERCLASS EVOLVED - FIN DE CODE ================================
