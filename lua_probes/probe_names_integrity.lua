-- Probe: playernames integrity.
-- For up to 200 sampled players, resolve firstnameid / lastnameid / commonnameid / playerjerseynameid
-- against the playernames dictionary and report unresolved counts.
-- Output: PROBE_names_integrity_DD_MM_YYYY.csv on Desktop.
require 'imports/other/helpers'

assert(IsInCM(), "Script must be executed in career mode")

local SAMPLE_SIZE = 200

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
local path = string.format("%s\\PROBE_names_integrity_%02d_%02d_%04d.csv",
                           desktop_path, d.day, d.month, d.year)

local f = io.open(path, "w+")
io.output(f)
io.write("probe,status,detail,sample_value\n")

-- Step 1: build nameid -> name cache from playernames.
local NAMES = {}
local name_count = 0
local ok_nt, nt = pcall(function() return LE.db:GetTable("playernames") end)
if not ok_nt or nt == nil then
    write_row("playernames_table", "MISSING", "LE.db:GetTable('playernames') failed", "")
    io.close(f)
    LOGGER:LogError("playernames table not accessible")
    return
end

local rec = nt:GetFirstRecord()
while rec > 0 do
    local ok_id, nameid = pcall(nt.GetRecordFieldValue, nt, rec, "nameid")
    local ok_nm, nm     = pcall(nt.GetRecordFieldValue, nt, rec, "name")
    if ok_id and nameid ~= nil then
        NAMES[nameid] = (ok_nm and nm) or ""
        name_count = name_count + 1
    end
    rec = nt:GetNextValidRecord()
end
write_row("playernames_cache", "OK", "rows_cached=" .. name_count, "")

-- Step 2: sample players and check resolution of each of the 4 nameid FKs.
local pt = LE.db:GetTable("players")
local processed = 0
local unresolved = { firstnameid = 0, lastnameid = 0, commonnameid = 0, playerjerseynameid = 0 }
local seen_zero  = { firstnameid = 0, lastnameid = 0, commonnameid = 0, playerjerseynameid = 0 }
local first_unresolved_sample = { firstnameid = "", lastnameid = "", commonnameid = "", playerjerseynameid = "" }

local prec = pt:GetFirstRecord()
while prec > 0 and processed < SAMPLE_SIZE do
    local ok_pid, pid = pcall(pt.GetRecordFieldValue, pt, prec, "playerid")
    if ok_pid and pid ~= nil then
        for _, col in ipairs({ "firstnameid", "lastnameid", "commonnameid", "playerjerseynameid" }) do
            local ok_v, v = pcall(pt.GetRecordFieldValue, pt, prec, col)
            if ok_v and v ~= nil then
                if v == 0 then
                    seen_zero[col] = seen_zero[col] + 1
                elseif NAMES[v] == nil then
                    unresolved[col] = unresolved[col] + 1
                    if first_unresolved_sample[col] == "" then
                        first_unresolved_sample[col] = "pid=" .. tostring(pid) .. ";" .. col .. "=" .. tostring(v)
                    end
                end
            end
        end
        processed = processed + 1
    end
    prec = pt:GetNextValidRecord()
end

write_row("sample_size", "OK", "players_sampled=" .. processed, "")
for _, col in ipairs({ "firstnameid", "lastnameid", "commonnameid", "playerjerseynameid" }) do
    local status = (unresolved[col] == 0) and "OK" or "UNRESOLVED"
    write_row(col .. "_resolution",
              status,
              "unresolved=" .. unresolved[col] .. ";zero_values=" .. seen_zero[col],
              first_unresolved_sample[col])
end

io.close(f)
LOGGER:LogInfo("probe_names_integrity done: " .. path)
