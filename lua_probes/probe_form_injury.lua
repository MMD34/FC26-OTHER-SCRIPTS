-- Probe: teamplayerlinks.form / teamplayerlinks.injury distribution.
-- Emits a histogram of observed values across all rows so the encoding (scale,
-- enum, 0-based?) can be inferred (PT §15.3).
-- Output: PROBE_form_injury_DD_MM_YYYY.csv on Desktop.
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
local path = string.format("%s\\PROBE_form_injury_%02d_%02d_%04d.csv",
                           desktop_path, d.day, d.month, d.year)

local f = io.open(path, "w+")
io.output(f)
io.write("probe,status,detail,sample_value\n")

local ok_tpl, tpl = pcall(function() return LE.db:GetTable("teamplayerlinks") end)
if not ok_tpl or tpl == nil then
    write_row("teamplayerlinks_table", "MISSING",
              "LE.db:GetTable('teamplayerlinks') failed", "")
    io.close(f)
    LOGGER:LogError("teamplayerlinks table not accessible")
    return
end

local form_hist = {}
local injury_hist = {}
local total = 0
local form_errors = 0
local injury_errors = 0

local rec = tpl:GetFirstRecord()
while rec > 0 do
    total = total + 1
    local ok_f, fv = pcall(tpl.GetRecordFieldValue, tpl, rec, "form")
    local ok_i, iv = pcall(tpl.GetRecordFieldValue, tpl, rec, "injury")
    if ok_f and fv ~= nil then
        form_hist[fv] = (form_hist[fv] or 0) + 1
    else
        form_errors = form_errors + 1
    end
    if ok_i and iv ~= nil then
        injury_hist[iv] = (injury_hist[iv] or 0) + 1
    else
        injury_errors = injury_errors + 1
    end
    rec = tpl:GetNextValidRecord()
end

write_row("total_rows", "OK", "rows=" .. total, "")
write_row("form_errors", (form_errors == 0) and "OK" or "WARN",
          "read_errors=" .. form_errors, "")
write_row("injury_errors", (injury_errors == 0) and "OK" or "WARN",
          "read_errors=" .. injury_errors, "")

-- Emit sorted histograms.
local function emit_hist(name, hist)
    local keys = {}
    for k, _ in pairs(hist) do keys[#keys + 1] = k end
    table.sort(keys, function(a, b) return (tonumber(a) or 0) < (tonumber(b) or 0) end)
    for _, k in ipairs(keys) do
        write_row(name .. "_bucket", "OK",
                  "value=" .. tostring(k),
                  "count=" .. tostring(hist[k]))
    end
end

emit_hist("form", form_hist)
emit_hist("injury", injury_hist)

io.close(f)
LOGGER:LogInfo("probe_form_injury done: " .. path)
