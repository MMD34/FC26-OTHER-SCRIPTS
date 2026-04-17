-- Probe: face-aggregate attributes (pacdiv, shohan, paskic, driref, defspe, phypos).
-- Dumps these 6 fields for 20 well-known players so the user can compare the values
-- to the in-game card and resolve the encoding (PT §15.2).
-- Output: PROBE_face_aggregates_DD_MM_YYYY.csv on Desktop.
require 'imports/other/helpers'

assert(IsInCM(), "Script must be executed in career mode")

-- TODO_ASK_USER: please provide up to 20 well-known `playerid`s here
-- (typically real, identifiable stars) so we can compare raw values with the
-- FC 26 in-game player card. Pause execution and ask the user if the list is
-- still empty.
local SAMPLE_PLAYERIDS = {
    -- TODO_ASK_USER: add playerids below, one per line, e.g.:
    -- 158023,  -- L. Messi
    -- 20801,   -- Cristiano Ronaldo
}

local FACE_COLS = { "pacdiv", "shohan", "paskic", "driref", "defspe", "phypos" }

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
local path = string.format("%s\\PROBE_face_aggregates_%02d_%02d_%04d.csv",
                           desktop_path, d.day, d.month, d.year)

local f = io.open(path, "w+")
io.output(f)
io.write("probe,status,detail,sample_value\n")

if #SAMPLE_PLAYERIDS == 0 then
    write_row("sample_list", "MISSING",
              "SAMPLE_PLAYERIDS is empty (TODO_ASK_USER) — ask user for playerids", "")
    io.close(f)
    LOGGER:LogError("probe_face_aggregates: SAMPLE_PLAYERIDS is empty")
    return
end

-- Build playerid -> record index map by scanning once.
local pt = LE.db:GetTable("players")
local WANTED = {}
for _, pid in ipairs(SAMPLE_PLAYERIDS) do WANTED[pid] = true end

local rec = pt:GetFirstRecord()
local found = 0
while rec > 0 do
    local ok_pid, pid = pcall(pt.GetRecordFieldValue, pt, rec, "playerid")
    if ok_pid and pid ~= nil and WANTED[pid] then
        local parts = { "playerid=" .. tostring(pid) }
        for _, col in ipairs(FACE_COLS) do
            local ok_v, v = pcall(pt.GetRecordFieldValue, pt, rec, col)
            if ok_v then
                parts[#parts + 1] = col .. "=" .. tostring(v)
            else
                parts[#parts + 1] = col .. "=<error>"
            end
        end
        write_row("face_aggregates", "OK",
                  "compare to in-game card",
                  table.concat(parts, ";"))
        found = found + 1
    end
    rec = pt:GetNextValidRecord()
end

write_row("summary", "OK",
          "found=" .. found .. "/" .. #SAMPLE_PLAYERIDS, "")

io.close(f)
LOGGER:LogInfo("probe_face_aggregates done: " .. path)
