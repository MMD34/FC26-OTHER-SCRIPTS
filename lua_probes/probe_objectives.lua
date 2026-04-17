-- Probe: leagueteamlinks objective semantics (PT §15.5).
-- Dumps objective-related fields for the user's team and up to 3 rivals
-- (rivals resolved via teams.rivalteam).
-- Output: PROBE_objectives_DD_MM_YYYY.csv on Desktop.
require 'imports/other/helpers'

assert(IsInCM(), "Script must be executed in career mode")

local OBJECTIVE_FIELDS = {
    "objective", "hasachievedobjective", "highestpossible", "highestprobable",
    "yettowin", "actualvsexpectations", "champion",
}

local function csv_escape(v)
    if v == nil then return "" end
    local s = tostring(v)
    if s:find('[,"\n]') then
        s = '"' .. s:gsub('"', '""') .. '"'
    end
    return s
end

local function write_row(probe, status, detail, sample_value)
    io.write(csv_escape(probe) .. "," .. csv_escape(status) .. "," ..
             csv_escape(detail) .. "," .. csv_escape(sample_value) .. "\n")
end

local desktop_path = string.format("%s\\Desktop", os.getenv('USERPROFILE'))
local d = GetCurrentDate()
local path = string.format("%s\\PROBE_objectives_%02d_%02d_%04d.csv",
                           desktop_path, d.day, d.month, d.year)

local f = io.open(path, "w+")
io.output(f)
io.write("probe,status,detail,sample_value\n")

local user_teamid = GetUserTeamID()
write_row("user_team", "OK", "GetUserTeamID()", "teamid=" .. tostring(user_teamid))

local teams_tbl = LE.db:GetTable("teams")
local ltl_tbl   = LE.db:GetTable("leagueteamlinks")

-- Collect rival teamids (up to 3) by scanning teams for rivalteam relations
-- involving the user's team. The `rivalteam` field is described in PT §4.6.
local rival_ids = {}

local function add_rival(tid)
    if tid == nil or tid == 0 or tid == user_teamid then return end
    for _, existing in ipairs(rival_ids) do
        if existing == tid then return end
    end
    if #rival_ids < 3 then
        rival_ids[#rival_ids + 1] = tid
    end
end

-- Strategy 1: read the user's own rivalteam pointer.
local tr = teams_tbl:GetFirstRecord()
while tr > 0 do
    local ok_id, tid = pcall(teams_tbl.GetRecordFieldValue, teams_tbl, tr, "teamid")
    if ok_id and tid == user_teamid then
        local ok_rv, rv = pcall(teams_tbl.GetRecordFieldValue, teams_tbl, tr, "rivalteam")
        if ok_rv then add_rival(rv) end
        break
    end
    tr = teams_tbl:GetNextValidRecord()
end

-- Strategy 2: scan teams for any that name the user as rival (reverse edge).
tr = teams_tbl:GetFirstRecord()
while tr > 0 and #rival_ids < 3 do
    local ok_rv, rv = pcall(teams_tbl.GetRecordFieldValue, teams_tbl, tr, "rivalteam")
    if ok_rv and rv == user_teamid then
        local ok_id, tid = pcall(teams_tbl.GetRecordFieldValue, teams_tbl, tr, "teamid")
        if ok_id then add_rival(tid) end
    end
    tr = teams_tbl:GetNextValidRecord()
end

local TARGETS = { user_teamid }
for _, rid in ipairs(rival_ids) do TARGETS[#TARGETS + 1] = rid end

write_row("rivals", "OK", "rivals_found=" .. #rival_ids,
          "ids=" .. table.concat(rival_ids, ";"))

-- Scan leagueteamlinks once, emitting rows for each target teamid.
local hit = {}
for _, tid in ipairs(TARGETS) do hit[tid] = false end

local rec = ltl_tbl:GetFirstRecord()
while rec > 0 do
    local ok_tid, tid = pcall(ltl_tbl.GetRecordFieldValue, ltl_tbl, rec, "teamid")
    if ok_tid and tid ~= nil and hit[tid] == false then
        local parts = { "teamid=" .. tostring(tid) }
        local ok_lid, lid = pcall(ltl_tbl.GetRecordFieldValue, ltl_tbl, rec, "leagueid")
        if ok_lid then parts[#parts + 1] = "leagueid=" .. tostring(lid) end
        for _, col in ipairs(OBJECTIVE_FIELDS) do
            local ok_v, v = pcall(ltl_tbl.GetRecordFieldValue, ltl_tbl, rec, col)
            if ok_v then
                parts[#parts + 1] = col .. "=" .. tostring(v)
            else
                parts[#parts + 1] = col .. "=<error>"
            end
        end
        local label = (tid == user_teamid) and "user_objectives" or "rival_objectives"
        write_row(label, "OK", "from leagueteamlinks", table.concat(parts, ";"))
        hit[tid] = true
    end
    rec = ltl_tbl:GetNextValidRecord()
end

for tid, was_found in pairs(hit) do
    if not was_found then
        write_row("missing_row", "WARN",
                  "teamid not found in leagueteamlinks",
                  "teamid=" .. tostring(tid))
    end
end

io.close(f)
LOGGER:LogInfo("probe_objectives done: " .. path)
