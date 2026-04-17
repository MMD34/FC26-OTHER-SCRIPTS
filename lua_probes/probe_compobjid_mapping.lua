-- Probe: compobjid <-> leagueid mapping (PT §15.6).
-- Emits one row per (compobjid, compname) from GetPlayersStats(), alongside
-- candidate (leagueid, leaguename) rows from the leagues table for cross-reference.
-- Output: PROBE_compobjid_mapping_DD_MM_YYYY.csv on Desktop.
require 'imports/other/helpers'

assert(IsInCM(), "Script must be executed in career mode")

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
local path = string.format("%s\\PROBE_compobjid_mapping_%02d_%02d_%04d.csv",
                           desktop_path, d.day, d.month, d.year)

local f = io.open(path, "w+")
io.output(f)
io.write("probe,status,detail,sample_value\n")

-- Step 1: unique (compobjid, compname) from GetPlayersStats().
local all_stats = GetPlayersStats()
local seen = {}
local comp_list = {}
for i = 1, #all_stats do
    local s = all_stats[i]
    local cid = s.compobjid
    local cname = s.compname
    if cid ~= nil and not seen[cid] then
        seen[cid] = true
        comp_list[#comp_list + 1] = { id = cid, name = cname }
    end
end

write_row("compobjids", "OK",
          "distinct_compobjids=" .. #comp_list, "")

for _, c in ipairs(comp_list) do
    write_row("comp_entry", "OK",
              "compobjid=" .. tostring(c.id),
              "compname=" .. tostring(c.name or ""))
end

-- Step 2: dump all leagues rows.
local leagues = LE.db:GetTable("leagues")
local rec = leagues:GetFirstRecord()
local league_count = 0
while rec > 0 do
    local ok_lid, lid = pcall(leagues.GetRecordFieldValue, leagues, rec, "leagueid")
    local ok_ln, ln  = pcall(leagues.GetRecordFieldValue, leagues, rec, "leaguename")
    local ok_lv, lv  = pcall(leagues.GetRecordFieldValue, leagues, rec, "level")
    if ok_lid then
        write_row("league_entry", "OK",
                  "leagueid=" .. tostring(lid),
                  "leaguename=" .. tostring((ok_ln and ln) or "") ..
                  ";level=" .. tostring((ok_lv and lv) or ""))
        league_count = league_count + 1
    end
    rec = leagues:GetNextValidRecord()
end

write_row("leagues_total", "OK", "leagues_count=" .. league_count, "")

io.close(f)
LOGGER:LogInfo("probe_compobjid_mapping done: " .. path)
