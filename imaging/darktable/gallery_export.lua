-- Export selected darktable images into this site's gallery tree.
--
-- Load from darktable with something like:
-- dofile("/Users/jsteward/work/jsteward.moe/imaging/darktable/gallery_export.lua")

local dt = require "darktable"

local DEFAULT_MAX_WIDTH = 3200
local AVIF_QUALITY = 60
local EXIFTOOL_ENV = os.getenv("EXIFTOOL")
local USER = os.getenv("USER") or os.getenv("LOGNAME")
local exiftool_prefix_cache = nil
local exiftool_paths_cache = nil

local function dirname(path)
  return path:match("^(.*)[/\\][^/\\]+$") or "."
end

local function basename(path)
  return path:match("([^/\\]+)$") or path
end

local function strip_extension(path)
  return path:gsub("%.[^.]*$", "")
end

local function shell_quote(value)
  return "'" .. tostring(value):gsub("'", "'\\''") .. "'"
end

local function file_exists(path)
  local file = io.open(path, "rb")
  if file then
    file:close()
    return true
  end
  return false
end

local function run(command)
  return dt.control.execute(command) == 0
end

local function command_ok(command)
  return run(command .. " >/dev/null 2>&1")
end

local function repo_root()
  local configured = os.getenv("GALLERY_REPO_ROOT")
  if configured and configured ~= "" then
    return configured:gsub("/$", "")
  end

  local source = debug.getinfo(1, "S").source:gsub("^@", "")
  return dirname(dirname(dirname(source)))
end

local ROOT = repo_root()
local GALLERY_DIR = ROOT .. "/content/images/gallery"

local function exiftool_prefix()
  if exiftool_prefix_cache then
    return exiftool_prefix_cache
  end

  local candidates = {}
  local function add_candidate(path)
    if path and path ~= "" then
      candidates[#candidates + 1] = path
    end
  end

  add_candidate(EXIFTOOL_ENV)
  add_candidate(USER and ("/etc/profiles/per-user/" .. USER .. "/bin/exiftool") or nil)
  add_candidate("exiftool")
  add_candidate("/opt/homebrew/bin/exiftool")
  add_candidate("/usr/local/bin/exiftool")
  add_candidate("/run/current-system/sw/bin/exiftool")
  add_candidate("/nix/var/nix/profiles/default/bin/exiftool")

  exiftool_paths_cache = {}
  for _, candidate in ipairs(candidates) do
    exiftool_paths_cache[#exiftool_paths_cache + 1] = candidate
    local prefix = shell_quote(candidate)
    if command_ok(prefix .. " -ver") then
      exiftool_prefix_cache = prefix
      return exiftool_prefix_cache
    end
  end

  return nil
end

local function exiftool_paths()
  if not exiftool_paths_cache then
    exiftool_prefix()
  end
  return table.concat(exiftool_paths_cache or {}, ", ")
end

local function title_from_id(id)
  local slug = id:gsub("^%d+%-", "")
  return (slug:gsub("%-", " "):gsub("(%a)([%w_']*)", function(first, rest)
    return first:upper() .. rest
  end))
end

local function scan_categories()
  local categories = {}
  local command = "find " .. shell_quote(GALLERY_DIR) .. " -mindepth 1 -maxdepth 1 -type d | sort"
  local pipe = io.popen(command, "r")

  if pipe then
    for path in pipe:lines() do
      local id = basename(path)
      if not id:match("^%.") then
        categories[#categories + 1] = {
          id = id,
          label = title_from_id(id) .. " (" .. id .. ")",
        }
      end
    end
    pipe:close()
  end

  return categories
end

local categories = scan_categories()
local category_picker = dt.new_widget("combobox") {
  label = "category",
  editable = false,
  tooltip = "Gallery category to receive the exported AVIF files",
}

for index, category in ipairs(categories) do
  category_picker[index] = category.label
end
category_picker.selected = #categories > 0 and 1 or 0

local width_label = dt.new_widget("label") {
  label = "max width",
}

local width_entry_ok, width_entry = pcall(function()
  return dt.new_widget("entry") {
    text = tostring(DEFAULT_MAX_WIDTH),
  }
end)

if not width_entry_ok then
  dt.print_error("gallery export: this darktable build rejected the width text input; using 3200")
  width_entry = dt.new_widget("label") {
    label = tostring(DEFAULT_MAX_WIDTH),
  }
end

local status_label = dt.new_widget("label") {
  label = #categories > 0
      and ("repo: " .. ROOT)
      or ("no gallery categories found under " .. GALLERY_DIR),
}

local function selected_category()
  local selected = category_picker.selected
  if selected < 1 then
    return nil
  end
  return categories[selected]
end

local function max_width()
  local ok, text = pcall(function()
    return width_entry.text
  end)
  local value = tonumber(ok and text or nil)
  if not value or value < 1 then
    pcall(function()
      width_entry.text = tostring(DEFAULT_MAX_WIDTH)
    end)
    return DEFAULT_MAX_WIDTH
  end
  value = math.floor(value)
  pcall(function()
    width_entry.text = tostring(value)
  end)
  return value
end

local function image_source_path(image)
  if image.path and image.filename then
    return image.path .. "/" .. image.filename
  end
  return tostring(image.filename or image)
end

local function destination_path(category, image)
  local source = image_source_path(image)
  local name = strip_extension(basename(source)):gsub("[^%w._-]+", "-")
  local directory = GALLERY_DIR .. "/" .. category.id
  return directory .. "/" .. name .. ".avif"
end

local function notify(message)
  if dt.print_toast then
    dt.print_toast(message)
  else
    dt.print(message)
  end
end

local function filtered_exif_command(source, destination, image)
  local function image_tag_args(image)
    local function read(name)
      local ok, value = pcall(function()
        return image[name]
      end)
      if not ok or value == nil or value == "" then
        return nil
      end
      return tostring(value)
    end

    local fields = {
      { "Make", read("exif_maker") },
      { "Model", read("exif_model") },
      { "LensModel", read("exif_lens") },
      { "FocalLength", read("exif_focal_length") },
      { "FNumber", read("exif_aperture") },
      { "ExposureTime", read("exif_exposure") },
      { "ISO", read("exif_iso") },
      { "DateTimeOriginal", read("exif_datetime_taken") },
    }

    local args = {}
    for _, field in ipairs(fields) do
      if field[2] then
        args[#args + 1] = shell_quote("-" .. field[1] .. "=" .. field[2])
      end
    end
    return table.concat(args, " ")
  end

  local tags = table.concat({
    "-Make",
    "-Model",
    "-LensMake",
    "-LensModel",
    "-FocalLength",
    "-FNumber",
    "-ExposureTime",
    "-ISO",
    "-ISOSpeedRatings",
    "-PhotographicSensitivity",
    "-DateTimeOriginal",
  }, " ")

  return table.concat({
    exiftool_prefix(),
    "-overwrite_original",
    "-P",
    "-all=",
    "-TagsFromFile", shell_quote(source),
    tags,
    image_tag_args(image),
    shell_quote(destination),
  }, " ")
end

local function export_image(image, category, width)
  local destination = destination_path(category, image)
  local format = dt.new_format("avif")

  format.max_width = width
  format.max_height = 0
  pcall(function() format.quality = AVIF_QUALITY end)
  pcall(function() format.bit_depth = 10 end)

  local ok, result = pcall(function()
    return format:write_image(image, destination, false)
  end)

  -- darktable 4.8's Lua API returns false on success; keep the file check as
  -- the authority so the script works across both old and new API behavior.
  if not ok or not file_exists(destination) then
    error("failed to export " .. image_source_path(image) .. ": " .. tostring(result))
  end

  local source = image_source_path(image)
  local metadata_ok = run(filtered_exif_command(source, destination, image))
  return destination, metadata_ok
end

local function export_selection()
  local category = selected_category()
  if not category then
    dt.print_error("gallery export: choose a category first")
    return
  end

  if not exiftool_prefix() then
    local message = "gallery export: exiftool not found; searched " .. exiftool_paths()
    status_label.label = message
    notify(message)
    dt.print_error(message)
    return
  end

  local images = dt.gui.action_images
  local total = #images
  if total == 0 then
    dt.print_error("gallery export: select one or more images first")
    return
  end

  local width = max_width()

  local exported = 0
  local metadata_failures = 0

  for _, image in ipairs(images) do
    local ok, destination, metadata_ok = pcall(export_image, image, category, width)
    if ok then
      exported = exported + 1
      local progress = exported .. "/" .. total .. " " .. basename(destination)
      status_label.label = progress
      notify("gallery export: " .. progress)
      if not metadata_ok then
        metadata_failures = metadata_failures + 1
        dt.print_error("gallery export: EXIF copy failed for " .. basename(destination))
      end
    else
      dt.print_error(destination)
    end
  end

  local message = "gallery export: " .. exported .. " AVIF file(s) to " .. category.id
  if metadata_failures > 0 then
    message = message .. " (" .. metadata_failures .. " missing filtered EXIF)"
  end
  status_label.label = message
  dt.print(message)
end

local export_button = dt.new_widget("button") {
  label = "export selected AVIF",
  tooltip = "Export action images as max-width 3200px AVIF files with caption EXIF",
  clicked_callback = export_selection,
}

local widget = dt.new_widget("box") {
  orientation = "vertical",
  category_picker,
  width_label,
  width_entry,
  export_button,
  status_label,
}

dt.register_lib(
  "jsteward_gallery_export",
  "gallery export",
  true,
  false,
  {
    [dt.gui.views.lighttable] = { "DT_UI_CONTAINER_PANEL_RIGHT_CENTER", 90 },
    [dt.gui.views.darkroom] = { "DT_UI_CONTAINER_PANEL_RIGHT_CENTER", 90 },
  },
  widget,
  nil,
  nil
)
