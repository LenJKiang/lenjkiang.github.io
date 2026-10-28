-- Pandoc's Windows Lua os.getenv returns ANSI bytes for Unicode paths.
-- Quarto 1.9 expects UTF-8 for this value before its filesystem wrapper.
-- Project-local compatibility filter; installed Quarto files are untouched.
if pandoc.system.os == 'mingw32' then
  local original_getenv = os.getenv
  local codepage = original_getenv('QUARTO_WIN_CODEPAGE') or '936'
  local dependency_file = original_getenv('QUARTO_FILTER_DEPENDENCY_FILE')
  if dependency_file then
    local ok, decoded = pcall(pandoc.text.fromencoding, dependency_file, 'CP' .. codepage)
    if ok then
      os.getenv = function(name)
        if name == 'QUARTO_FILTER_DEPENDENCY_FILE' then return decoded end
        return original_getenv(name)
      end
    end
  end
end
