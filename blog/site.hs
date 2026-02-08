{-# LANGUAGE BangPatterns #-}
{-# LANGUAGE BlockArguments #-}
{-# LANGUAGE ImportQualifiedPost #-}
{-# LANGUAGE LambdaCase #-}
{-# LANGUAGE OverloadedStrings #-}
{-# LANGUAGE ScopedTypeVariables #-}
{-# LANGUAGE ViewPatterns #-}

--------------------------------------------------------------------------------

import Control.Monad ((<=<))
import Data.ByteString.Lazy qualified as BS
import Data.Functor ((<&>))
import Data.List (intercalate, isPrefixOf, isSuffixOf)
import Data.Maybe (fromMaybe)
import Data.Text (Text)
import Data.Text qualified as T
import Data.Text.IO qualified as T
import GHC.IO.Handle (BufferMode (NoBuffering), Handle, hSetBuffering)
import Hakyll
import Skylighting.Styles (parseTheme)
import System.FilePath (takeFileName)
import System.Process (runInteractiveCommand)
import Text.Pandoc (Block (..), Extension (..), HTMLMathMethod (..), Inline (..), MathType (..), Pandoc, ReaderOptions (..), WriterOptions (..), extensionsFromList)
import Text.Pandoc.Builder (HasMeta (..), Many, simpleTable)
import Text.Pandoc.Builder qualified as Many (singleton, toList)
import Text.Pandoc.Highlighting (styleToCss)
import Text.Pandoc.SideNote (usingSideNotes)
import Text.Pandoc.Templates (compileTemplate)
import Text.Pandoc.Walk (walk, walkM)

--------------------------------------------------------------------------------
-- Haskyll entrypoint.
main :: IO ()
main = hakyllWith configuration $ do
    -- Static assets
    match
        ( "images/**"
            .||. "fonts/**"
            .||. "robots.txt"
            .||. "favicon.svg"
            .||. ".well-known/**"
            .||. "CNAME"
            .||. "publickey.txt"
            .||. "pp.jpg"
        )
        $ do
            route idRoute
            compile copyFileCompiler

    -- CSS compression
    match "css/*" $ do
        route idRoute
        compile compressCssCompiler

    -- Bibliography
    match "bib/style.csl" $ compile cslCompiler
    match "bib/bibliography.bib" $ compile biblioCompiler

    -- Non-posts markdown
    match
        ( "about.md"
            .||. "contact.md"
            .||. "404.md"
        )
        $ do
            route $ setExtension "html"
            compile $
                pandocCompiler'
                    >>= loadAndApplyTemplate "templates/default.html" defaultContext
                    >>= relativizeUrls

    -- build up tags
    tags <- buildTags "posts/*.md" (fromCapture "tags/*.html")
    tagsRules tags $ \tag pat -> do
        let title = "Posts tagged \"" ++ tag ++ "\""
        route idRoute
        compile $ do
            posts <- recentFirst =<< loadAll pat
            let ctx =
                    constField "title" title
                        `mappend` listField "posts" (postCtxWithTags tags) (return posts)
                        `mappend` defaultContext

            makeItem ""
                >>= loadAndApplyTemplate "templates/tags.html" ctx
                >>= loadAndApplyTemplate "templates/default.html" ctx
                >>= relativizeUrls

    -- Posts markdown
    match "posts/*.md" $ do
        route $ setExtension "html"
        compile $ do
            tocCtx <- getTocCtx (postCtxWithTags tags)
            pandocCompiler'
                >>= loadAndApplyTemplate "templates/post.html" tocCtx
                >>= saveSnapshot "content"
                >>= loadAndApplyTemplate "templates/default.html" tocCtx
                >>= relativizeUrls

    -- Archive
    create ["archive.html"] $ do
        route idRoute
        compile $ do
            posts <- recentFirst =<< loadAll "posts/*"
            let archiveCtx =
                    listField "posts" postCtx (return posts)
                        `mappend` constField "title" "Archives"
                        `mappend` defaultContext

            makeItem ""
                >>= loadAndApplyTemplate "templates/archive.html" archiveCtx
                >>= loadAndApplyTemplate "templates/default.html" archiveCtx
                >>= relativizeUrls

    -- Atom/RSS Feed
    create ["atom.xml"] $ do
        route idRoute
        compile $ do
            let feedCtx = postCtx `mappend` bodyField "description"
            posts <- fmap (take 10) . recentFirst =<< loadAllSnapshots "posts/*" "content"
            renderAtom myFeedConfiguration feedCtx posts

    -- Syntax Highlighting
    create ["css/syntax.css"] $ do
        route idRoute
        compile $ do
            makeItem $
                intercalate
                    "\n"
                    [ "@import \"syntax-light.css\" all and (prefers-color-scheme: light);"
                    , "@import \"syntax-dark.css\" all and (prefers-color-scheme: dark);"
                    , ""
                    ]
    -- Syntax highlighting in light mode.
    create ["css/syntax-light.css"] $ do
        route idRoute
        compile $ do
            themeContent <- unsafeCompiler $ BS.readFile "themes/gruvbox-light.theme"
            case parseTheme themeContent of
                Left err -> fail $ "Failed to parse light theme: " ++ err
                Right style -> makeItem $ styleToCss style

    -- Syntax highlighting in dark mode.
    create ["css/syntax-dark.css"] $ do
        route idRoute
        compile $ do
            themeContent <- unsafeCompiler $ BS.readFile "themes/gruvbox-dark.theme"
            case parseTheme themeContent of
                Left err -> fail $ "Failed to parse dark theme: " ++ err
                Right style -> makeItem $ styleToCss style

    -- Root index.html
    match "index.html" $ do
        route idRoute
        compile $ do
            posts <- fmap (take 10) . recentFirst =<< loadAll "posts/*"
            let indexCtx =
                    listField "posts" postCtx (return posts)
                        `mappend` defaultContext

            getResourceBody
                >>= applyAsTemplate indexCtx
                >>= loadAndApplyTemplate "templates/default.html" indexCtx
                >>= relativizeUrls

    -- Templates
    match "templates/*" $ compile templateBodyCompiler

--------------------------------------------------------------------------------
-- Post context, adds a date to the default context.
postCtx :: Context String
postCtx =
    dateField "date" "%B %e, %Y"
        `mappend` boolField "is-post" (const True)
        `mappend` defaultContext

postCtxWithTags :: Tags -> Context String
postCtxWithTags tags = tagsField "tags" tags `mappend` postCtx

--------------------------------------------------------------------------------
-- Configuration
configuration :: Configuration
configuration = defaultConfiguration{ignoreFile = ignoreFile'}
  where
    ignoreFile' path
        | "." `isPrefixOf` fileName = False -- give my .well-known stuff
        | "#" `isPrefixOf` fileName = True
        | "~" `isSuffixOf` fileName = True
        | ".swp" `isSuffixOf` fileName = True
        | otherwise = False
      where
        fileName = takeFileName path

--------------------------------------------------------------------------------
-- RSS
myFeedConfiguration :: FeedConfiguration
myFeedConfiguration =
    FeedConfiguration
        { feedTitle = "Jose Storopoli, PhD"
        , feedDescription = "Personal website of Jose Storopoli, PhD"
        , feedAuthorName = "Jose Storopoli, PhD"
        , feedAuthorEmail = "jose@storopoli.com"
        , feedRoot = "https://storopoli.com"
        }

--------------------------------------------------------------------------------
-- Table of Contents

-- | Text conversion utility function
asTxt :: (Text -> Text) -> String -> String
asTxt f = T.unpack . f . T.pack

-- | Create a context that contains a table of contents.
getTocCtx :: Context a -> Compiler (Context a)
getTocCtx ctx = do
    noToc <- (Just "true" ==) <$> (getUnderlying >>= (`getMetadataField` "no-toc"))
    bib <- (Just "true" ==) <$> (getUnderlying >>= (`getMetadataField` "bib"))
    writerOpts <- mkTocWriter myWriter
    toc <- renderPandocWith myReader writerOpts =<< getResourceBody
    pure $
        mconcat
            [ ctx
            , constField "toc" $
                (if bib then addBibHeading else id) $
                    killLinkIds (itemBody toc)
            , if noToc then boolField "no-toc" (pure noToc) else mempty
            ]
  where
    mkTocWriter :: WriterOptions -> Compiler WriterOptions
    mkTocWriter writerOpts = do
        tmpl <- either (const Nothing) Just <$> unsafeCompiler (compileTemplate "" "$toc$")
        dpth <- fromMaybe 3 <$> (getUnderlying >>= (`getMetadataField` "toc-depth") <&> fmap read)
        pure $
            writerOpts
                { writerTableOfContents = True
                , writerTOCDepth = dpth
                , writerTemplate = tmpl
                }

{- | Remove duplicate IDs from table of contents to avoid HTML validation issues.
Pandoc adds IDs for ToC elements, but having multiple ToCs can create duplicates.
-}
killLinkIds :: String -> String
killLinkIds = asTxt (mconcat . go . T.splitOn "id=\"toc-")
  where
    go :: [Text] -> [Text]
    go = \case
        [] -> []
        x : xs -> x : map (T.drop 1 . T.dropWhile (/= '\"')) xs

-- | Add a bibliography heading to the ToC if needed.
addBibHeading :: String -> String
addBibHeading = asTxt \s ->
    let (before, after) = T.breakOnEnd "</ul>" s
     in mconcat
            [ T.dropEnd 5 before
            , "<li><a href=\"#refs\">References</a></li></ul>"
            , after
            ]

--------------------------------------------------------------------------------
-- COMPILERS --

-- Custom Writer Options
myWriter :: WriterOptions
myWriter =
    defaultHakyllWriterOptions
        { writerHTMLMathMethod = KaTeX ""
        }

-- Custom Reader Options
myReader :: ReaderOptions
myReader =
    defaultHakyllReaderOptions
        { readerExtensions =
            readerExtensions defaultHakyllReaderOptions
                <> extensionsFromList [Ext_tex_math_single_backslash]
        }

-- Custom pandoc compiler render functions that work with Item Pandoc
myRenderPandocWithTransformM ::
    ReaderOptions ->
    WriterOptions ->
    (Item Pandoc -> Compiler (Item Pandoc)) ->
    Item String ->
    Compiler (Item String)
myRenderPandocWithTransformM ropt wopt f i =
    writePandocWith wopt <$> (f =<< readPandocWith ropt i)

-- Custom pandoc compiler writer functions that work with Item Pandoc
myPandocCompilerWithTransformM ::
    ReaderOptions ->
    WriterOptions ->
    (Item Pandoc -> Compiler (Item Pandoc)) ->
    Compiler (Item String)
myPandocCompilerWithTransformM ropt wopt f =
    getResourceBody >>= myRenderPandocWithTransformM ropt wopt f

-- KaTeX server side rendering
hlKaTeX :: Pandoc -> Compiler Pandoc
hlKaTeX pandoc = recompilingUnsafeCompiler do
    (hin, hout, _, _) <- runInteractiveCommand "deno run --import-map=import_map.json --no-remote scripts/math.ts"
    hSetBuffering hin NoBuffering
    hSetBuffering hout NoBuffering

    (`walkM` pandoc) \case
        Math mathType (T.unwords . T.lines . T.strip -> text) -> do
            let math :: Text =
                    foldl'
                        (\str (repl, with) -> T.replace repl with str)
                        case mathType of
                            DisplayMath {-s-} -> ":DISPLAY " <> text
                            InlineMath {-s-} -> text
                        macros
            T.hPutStrLn hin math
            RawInline "html" <$> getResponse hout
        block -> pure block
  where
    -- KaTeX might sent the input back as multiple lines if it involves a
    -- matrix of coordinates. The big assumption here is that it does so only
    -- when matrices—or other such constructs—are involved, and not when it
    -- sends back "normal" HTML.
    getResponse :: Handle -> IO Text
    getResponse handle = go ""
      where
        go :: Text -> IO Text
        go !str = do
            more <- (str <>) <$> T.hGetLine handle
            if ">" `T.isSuffixOf` more -- end of HTML snippet
                then pure more
                else go more

    -- I know that one could supply macros to KaTeX directly, but where is the
    -- fun in that‽
    macros :: [(Text, Text)]
    macros =
        [ ("≔", "\\mathrel{\\vcenter{:}}=")
        , ("\\defeq", "\\mathrel{\\vcenter{:}}=")
        , ("\\to", "\\longrightarrow")
        , ("\\mapsto", "\\longmapsto")
        , ("\\cat", "\\mathcal")
        , ("\\kVect", "\\mathsf{Vect}_{\\mathtt{k}}")
        ]

-- Bibliography processing
processBib :: Item Pandoc -> Compiler (Item Pandoc)
processBib pandoc = do
    csl <- load "bib/style.csl"
    bib <- load "bib/bibliography.bib"
    -- We do want to link citations.
    p <- withItemBody (pure . setMeta "link-citations" True) pandoc
    fmap tableiseBib <$> processPandocBiblio csl bib p

-- | Align all citations in a table and add References header.
tableiseBib :: Pandoc -> Pandoc
tableiseBib = walk \case
    -- Citations start with a <div id="refs" …>
    Div a@("refs", _, _) body ->
        -- Add h2 header and table with citations
        Div a $
            Header 2 ("", [], []) [Str "References"]
                : Many.toList (simpleTable [] (map citToRow body))
    body -> body
  where
    citToRow :: Block -> [Many Block]
    citToRow =
        map Many.singleton . \case
            Div attr [Para [s1, s2]] ->
                [Div attr [Plain [s1]], Plain [Space], Plain [s2]]
            _ -> error "citToRow: unexpected citation format."

-- Custom pandocCompiler with all compilers
pandocCompiler' :: Compiler (Item String)
pandocCompiler' =
    myPandocCompilerWithTransformM
        myReader
        myWriter
        ( traverse (pure . usingSideNotes <=< hlKaTeX)
            <=< processBib
        )

--------------------------------------------------------------------------------
