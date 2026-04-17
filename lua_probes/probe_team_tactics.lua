-- Probe: team tactics / formation tables (PT §15.4).
-- Tries to open several candidate table names via pcall; for each that exists,
-- dumps the list of column names observable on the first record.
-- Output: PROBE_team_tactics_DD_MM_YYYY.csv on Desktop.
require 'imports/other/helpers'

assert(IsInCM(), "Script must be executed in career mode")

local CANDIDATE_TABLES = {
    "teamsheets", "formations", "teamformations", "team_tactics",
}

-- Column names to attempt against the first record of each table. We try a
-- broad net of plausible names; successful reads confirm presence.
local CANDIDATE_COLUMNS = {
    "teamsheetid", "formationid", "formationname", "teamid",
    "buildupplay", "defensivedepth", "attackingwidth", "defensivewidth",
    "tacticid", "tacticname", "name", "id",
    "position1", "position2", "position3", "position4", "position5",
    "position6", "position7", "position8", "position9", "position10", "position11",
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
local path = string.format("%s\\PROBE_team_tactics_%02d_%02d_%04d.csv",
                           desktop_path, d.day, d.month, d.year)

local f = io.open(path, "w+")
io.output(f)
io.write("probe,status,detail,sample_value\n")

-- Also probe `teams.favoriteteamsheetid` availability on a single team record.
local ok_teams, teams = pcall(function() return LE.db:GetTable("teams") end)
if ok_teams and teams ~= nil then
    local t_rec = teams:GetFirstRecord()
    if t_rec > 0 then
        local ok_fts, fts = pcall(teams.GetRecordFieldValue, teams, t_rec, "favoriteteamsheetid")
        if ok_fts then
            write_row("teams.favoriteteamsheetid", "OK",
                      "read from first teams record",
                      "value=" .. tostring(fts))
        else
            write_row("teams.favoriteteamsheetid", "ERROR",
                      "field read failed", "")
        end
    end
end

for _, tname in ipairs(CANDIDATE_TABLES) do
    local ok, tbl = pcall(function() return LE.db:GetTable(tname) end)
    if not ok or tbl == nil then
        write_row("table:" .. tname, "MISSING",
                  "LE.db:GetTable failed", "")
    else
        local rec = tbl:GetFirstRecord()
        if rec <= 0 then
            write_row("table:" .. tname, "EMPTY",
                      "table opened but no first record", "")
        else
            write_row("table:" .. tname, "OK",
                      "opened; probing candidate columns", "")
            local found_cols = {}
            for _, col in ipairs(CANDIDATE_COLUMNS) do
                local ok_c, v = pcall(tbl.GetRecordFieldValue, tbl, rec, col)
                if ok_c and v ~= nil then
                    found_cols[#found_cols + 1] = col .. "=" .. tostring(v)
                end
            end
            if #found_cols > 0 then
                write_row("table:" .. tname .. ":columns", "OK",
                          "columns confirmed on first record",
                          table.concat(found_cols, ";"))
            else
                write_row("table:" .. tname .. ":columns", "WARN",
                          "none of the candidate columns matched", "")
            end
        end
    end
end

io.close(f)
LOGGER:LogInfo("probe_team_tactics done: " .. path)
